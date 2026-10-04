#!/usr/bin/env python3
"""Local fal/Higgsfield queue receipts. No scheduler, uploads, or live-test claims."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

HOSTS = {'fal': 'queue.fal.run', 'higgsfield': 'api.higgsfield.ai'}
TERMINAL = {'completed', 'failed', 'rejected', 'canceled'}

class ApiError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(f'Provider HTTP {code}; inspect provider dashboard without exposing credentials.')

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Provider redirect rejected; verify the documented endpoint.')

def safe_url(provider, url):
    if not isinstance(url, str):
        raise ValueError('Missing provider operation URL.')
    p = urllib.parse.urlsplit(url)
    if p.scheme != 'https' or p.hostname != HOSTS[provider] or p.username or p.password or p.port not in (None, 443) or p.fragment:
        raise ValueError('Unexpected provider operation URL; credentials were not sent.')
    return url

def model_path(value):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_./-]{0,249}', value) or any(x in ('', '.', '..') for x in value.split('/')):
        raise ValueError('Use an exact model path from current provider documentation.')
    return value

def credentials(provider):
    if provider == 'fal':
        value = os.environ.get('FAL_KEY', '')
    else:
        key = os.environ.get('HF_API_KEY_ID', '')
        secret = os.environ.get('HF_API_KEY_SECRET', '')
        value = f'{key}:{secret}' if key and secret else ''
    if not value or '\n' in value or '\r' in value:
        raise ValueError('Required server-side provider credentials are missing or invalid.')
    return 'Key ' + value

def account_hash(auth):
    return hashlib.sha256(auth.encode()).hexdigest()

def request(provider, method, url, auth, body=None, extra_headers=None):
    safe_url(provider, url)
    headers = {'Authorization': auth, 'Accept': 'application/json'}
    headers.update(extra_headers or {})
    encoded = None
    if body is not None:
        encoded = json.dumps(body, allow_nan=False).encode()
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(url, data=encoded, headers=headers, method=method)
    try:
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=30) as resp:
            raw = resp.read(8 * 1024 * 1024 + 1)
            if len(raw) > 8 * 1024 * 1024:
                raise ValueError('Provider JSON response exceeded the local client limit.')
            data = json.loads(raw) if raw else {}
            if not isinstance(data, dict):
                raise ValueError('Expected a provider JSON object.')
            return resp.status, data
    except urllib.error.HTTPError as exc:
        raise ApiError(exc.code) from None
    except urllib.error.URLError:
        raise RuntimeError('Provider network request failed; reconcile a submission before retrying.') from None

class Ledger:
    def __init__(self, path):
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if p.is_symlink():
            raise ValueError('Ledger symlinks are not allowed.')
        self.db = sqlite3.connect(p, timeout=10)
        os.chmod(p, 0o600)
        self.db.execute('CREATE TABLE IF NOT EXISTS jobs (operation TEXT PRIMARY KEY, signature TEXT NOT NULL, state TEXT NOT NULL, data TEXT NOT NULL, updated REAL NOT NULL)')
        self.db.commit()

    def close(self):
        self.db.close()

    def get(self, operation):
        row = self.db.execute('SELECT data FROM jobs WHERE operation=?', (operation,)).fetchone()
        if not row:
            raise ValueError('Unknown operation key.')
        return json.loads(row[0])

    def insert(self, data, signature):
        try:
            with self.db:
                self.db.execute('INSERT INTO jobs VALUES (?,?,?,?,?)', (data['operation'], signature, data['state'], json.dumps(data), time.time()))
            return True
        except sqlite3.IntegrityError:
            row = self.db.execute('SELECT signature FROM jobs WHERE operation=?', (data['operation'],)).fetchone()
            if row[0] != signature:
                raise ValueError('Operation key already belongs to a different input, account, model, or budget.')
            return False

    def save(self, data):
        with self.db:
            self.db.execute('UPDATE jobs SET state=?, data=?, updated=? WHERE operation=?', (data['state'], json.dumps(data), time.time(), data['operation']))
        return data


def submit(ledger, provider, model, payload, operation, max_usd, authorized=False):
    if not authorized:
        raise ValueError('Submission requires existing user authorization and --authorized acknowledgment.')
    if not isinstance(payload, dict) or not operation.strip() or len(operation) > 200:
        raise ValueError('Supply a JSON object and a bounded operation key.')
    if not math.isfinite(max_usd) or max_usd < 0:
        raise ValueError('Supply a finite, nonnegative authorized upper bound.')
    model_path(model)
    auth = credentials(provider)
    fingerprint = account_hash(auth)
    signature = hashlib.sha256(json.dumps([provider, model, payload, fingerprint, max_usd], sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    data = {'operation': operation, 'provider': provider, 'model': model, 'input_hash': hashlib.sha256(json.dumps(payload, sort_keys=True, allow_nan=False).encode()).hexdigest(), 'account_hash': fingerprint, 'max_usd': max_usd, 'state': 'submission_unknown', 'request_id': None, 'created_at': time.time(), 'artifact_verified': False}
    # One key per intended generation, even when two attempts have identical input.
    # Persist it before POST so an ambiguous submission can be reconciled.
    if provider == 'higgsfield':
        data['idempotency_key'] = str(uuid.uuid4())
    if not ledger.insert(data, signature):
        data = ledger.get(operation)
        if not data.get('request_id'):
            raise ValueError('Submission unresolved or rejected. Reconcile with provider; this key cannot create another generation.')
        return data
    url = f'https://{HOSTS[provider]}/{model}'
    extra = {'Idempotency-Key': data['idempotency_key']} if provider == 'higgsfield' else {}
    try:
        _, receipt = request(provider, 'POST', url, auth, payload, extra)
        if not isinstance(receipt.get('request_id'), str) or not receipt['request_id']:
            raise ValueError('Submission response lacks a request ID; reconcile with provider.')
        # Save the ID before validating any other returned field.
        data.update(request_id=receipt['request_id'], receipt=receipt, state='submitted')
        ledger.save(data)
        for key in ('status_url', 'cancel_url'):
            safe_url(provider, receipt.get(key))
        if provider == 'fal':
            safe_url(provider, receipt.get('response_url'))
        return data
    except ApiError as exc:
        if exc.code in (400, 401, 403, 404, 422):
            data['state'] = 'rejected'
        ledger.save(data)
        raise
    except Exception:
        ledger.save(data)
        raise


def normalize(provider, response):
    raw = response.get('status')
    if provider == 'fal':
        if raw == 'COMPLETED':
            return 'failed' if response.get('error') or response.get('error_type') else 'completed'
        mapping = {'IN_QUEUE': 'queued', 'IN_PROGRESS': 'running'}
    else:
        mapping = {'queued': 'queued', 'in_progress': 'running', 'completed': 'completed', 'failed': 'failed', 'nsfw': 'rejected', 'canceled': 'canceled'}
    return mapping.get(raw, 'unknown_provider_state')


def status(ledger, operation):
    data = ledger.get(operation)
    if data['state'] in TERMINAL:
        return data
    if not data.get('request_id'):
        raise ValueError('No provider request ID; reconcile the ambiguous submission first.')
    provider = data['provider']
    auth = credentials(provider)
    if account_hash(auth) != data['account_hash']:
        raise ValueError('Provider credential binding changed; verify account ownership before migration.')
    _, response = request(provider, 'GET', data['receipt']['status_url'], auth)
    state = normalize(provider, response)
    if response.get('request_id') not in (None, data['request_id']):
        raise ValueError('Provider response request ID mismatch.')
    data['provider_status'] = response
    # Do not release a pending cancellation just because a poll still sees work.
    data['state'] = 'cancel_requested' if data['state'] == 'cancel_requested' and state not in TERMINAL else state
    if state == 'completed' and provider == 'fal':
        # Until result retrieval succeeds, allow future polls to recover it.
        data['state'] = 'waiting_result'
        ledger.save(data)
        _, result = request(provider, 'GET', data['receipt']['response_url'], auth)
        data['result'] = result
        data['state'] = 'failed' if result.get('error') or result.get('error_type') else 'completed'
    elif state == 'completed':
        data['result'] = response
    return ledger.save(data)


def cancel(ledger, operation):
    data = ledger.get(operation)
    if data['state'] in TERMINAL:
        return data
    if not data.get('request_id'):
        raise ValueError('No provider request ID; reconcile before cancellation.')
    provider = data['provider']
    auth = credentials(provider)
    if account_hash(auth) != data['account_hash']:
        raise ValueError('Provider credential binding changed; verify account ownership before migration.')
    code, response = request(provider, 'PUT' if provider == 'fal' else 'POST', data['receipt']['cancel_url'], auth)
    if code != 202:
        raise ValueError('Cancellation not confirmed; reconcile provider status.')
    data.update(state='cancel_requested' if provider == 'fal' else 'canceled', cancellation=response)
    return ledger.save(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', required=True)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('submit')
    p.add_argument('--provider', choices=HOSTS, required=True)
    p.add_argument('--model', required=True)
    p.add_argument('--input', required=True)
    p.add_argument('--operation', required=True)
    p.add_argument('--max-usd', type=float, required=True)
    p.add_argument('--authorized', action='store_true')
    for command in ('status', 'cancel', 'inspect'):
        sub.add_parser(command).add_argument('--operation', required=True)
    args = parser.parse_args()
    ledger = Ledger(args.db)
    try:
        if args.command == 'submit':
            input_path = Path(args.input)
            if input_path.stat().st_size > 4 * 1024 * 1024:
                raise ValueError('Input JSON too large; use provider-supported uploaded media references.')
            result = submit(ledger, args.provider, args.model, json.loads(input_path.read_text()), args.operation, args.max_usd, args.authorized)
        elif args.command == 'status':
            result = status(ledger, args.operation)
        elif args.command == 'cancel':
            result = cancel(ledger, args.operation)
        else:
            result = ledger.get(args.operation)
        if args.command == 'inspect':
            print(json.dumps(result, indent=2))
        else:
            print(json.dumps({k: result.get(k) for k in ('operation', 'provider', 'state', 'request_id', 'artifact_verified')}))
    finally:
        ledger.close()

if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError, ApiError, OSError, sqlite3.Error) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
