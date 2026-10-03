#!/usr/bin/env python3
"""Private candidate 0.2.0. Compare supplied assertions without taking action.

Times establish consistency against supplied times, not live freshness.
Tree digests must cover selected paths and contents, including relevant
untracked files. Operators collect evidence and define scope in subject.
Effectiveness is unmeasured. No incident-prevention guarantee is made.
"""
import argparse
import json
import math
import os
import re
import stat
import sys
from datetime import datetime

LIMIT = 1024 * 1024
KINDS = ('head', 'tree', 'test', 'action', 'process', 'approval', 'capability')
FIELDS = {
    'head': (), 'tree': (), 'test': ('head', 'tree', 'command'),
    'action': ('operation_id',), 'process': ('pid', 'start_token', 'owner'),
    'approval': ('artifact_sha256',), 'capability': ('operation', 'model'),
}
NOTICE = ('Advisory only. Supplied evidence is not authenticated. '
          'Matching listed claims does not authorize any action.')
HOLD = ('Hold. Verify current effects before any further action. '
        'This is not proof of completion and does not authorize replay.')


class InputError(ValueError):
    pass


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def digest(value, lengths=(64,)):
    return (isinstance(value, str) and len(value) in lengths
            and re.fullmatch('[0-9a-f]+', value) is not None)


def timestamp(value):
    if not isinstance(value, str) or not re.fullmatch(
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z', value):
        raise InputError('Invalid UTC timestamp.')
    try:
        return datetime.fromisoformat(value[:-1] + '+00:00')
    except ValueError:
        raise InputError('Invalid UTC timestamp.') from None


def json_types(value):
    """Reject non-JSON values supplied directly through the import API."""
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float and math.isfinite(value):
        return
    if type(value) is list:
        for item in value:
            json_types(item)
        return
    if type(value) is dict and all(type(key) is str for key in value):
        for item in value.values():
            json_types(item)
        return
    raise InputError('Input must contain only JSON values.')


def path_key(key):
    return key.replace('~', '~0').replace('/', '~1')


def unknown_fields(obj, allowed, path, diagnostics):
    for key in obj:
        if key not in allowed:
            diagnostics.append((path + '/' + path_key(key),
                                'Unknown field at this path.'))


def packet(root, collection, time_field, label, diagnostics):
    if type(root) is not dict:
        raise InputError('Packet root must be an object.')
    if type(root.get('schema_version')) is not int or root['schema_version'] != 1:
        raise InputError('Unsupported schema version.')
    moment = timestamp(root.get(time_field))
    items = root.get(collection)
    if type(items) is not list or len(items) > 100:
        raise InputError('Items must be an array with at most 100 entries.')
    if collection == 'claims' and not items:
        raise InputError('Claims must not be empty.')
    unknown_fields(root, ('schema_version', time_field, collection), label, diagnostics)
    ids = set()
    for index, item in enumerate(items):
        if type(item) is not dict:
            raise InputError('Each item must be an object.')
        if any(not nonempty(item.get(key)) for key in ('id', 'kind', 'subject')):
            raise InputError('Invalid required identifier, kind or subject.')
        if item['kind'] not in KINDS:
            raise InputError('Unsupported item kind.')
        if item['id'] in ids:
            raise InputError('Duplicate item identifier.')
        ids.add(item['id'])
        path = label + '/' + collection + '/' + str(index)
        allowed = ('id', 'kind', 'subject', 'value', 'binding')
        if collection == 'observations':
            allowed += ('source', 'observed_at', 'evidence')
        unknown_fields(item, allowed, path, diagnostics)
        if type(item.get('binding')) is dict:
            unknown_fields(item['binding'], FIELDS[item['kind']],
                           path + '/binding', diagnostics)
        value_fields = {'action': ('outcome', 'idempotent'), 'process': ('state',)}
        if type(item.get('value')) is dict:
            unknown_fields(item['value'], value_fields.get(item['kind'], ()),
                           path + '/value', diagnostics)
    return items, moment


def valid_record(item):
    kind, value, binding = item['kind'], item.get('value'), item.get('binding')
    if 'value' not in item or type(binding) is not dict:
        return False
    required = FIELDS[kind]
    if kind == 'process' and type(value) is dict and value.get('state') == 'missing':
        return binding == {} and set(value) == {'state'}
    if set(binding) != set(required):
        return False
    if kind == 'head':
        return digest(value, (40, 64))
    if kind == 'tree':
        return digest(value)
    if kind == 'test':
        return (value in ('passed', 'failed') and digest(binding['head'], (40, 64))
                and digest(binding['tree']) and nonempty(binding['command']))
    if kind == 'action':
        return (type(value) is dict and set(value) == {'outcome', 'idempotent'}
                and value['outcome'] in ('done', 'not_started', 'uncertain')
                and (value['idempotent'] is None or type(value['idempotent']) is bool)
                and nonempty(binding['operation_id']))
    if kind == 'process':
        return (type(value) is dict and set(value) == {'state'}
                and value['state'] in ('running', 'starting')
                and type(binding['pid']) is int and binding['pid'] > 0
                and nonempty(binding['start_token']) and nonempty(binding['owner']))
    if kind == 'approval':
        return value in ('granted', 'denied') and digest(binding['artifact_sha256'])
    return (value in ('success', 'failure')
            and all(nonempty(binding[key]) for key in required))


def evidence_error(item, saved, as_of, max_age):
    if not nonempty(item.get('source')):
        return 'Missing or invalid source label.'
    if item.get('evidence') not in ('receipt', 'metadata'):
        return 'Missing or invalid evidence category.'
    try:
        moment = timestamp(item.get('observed_at'))
    except InputError:
        return 'Missing or invalid observation time.'
    if moment > as_of or moment < saved:
        return 'Observation time is inconsistent with supplied packet times.'
    if (as_of - moment).total_seconds() > max_age:
        return 'Observation exceeds the supplied time age limit.'
    if item['kind'] in ('test', 'action', 'approval', 'capability'):
        if item['evidence'] != 'receipt':
            return 'A supplied receipt is required. Metadata is insufficient.'
    return None


def test_source_error(claim, observation, observations, saved, as_of, max_age):
    sources = {}
    for kind in ('head', 'tree'):
        matches = [item for item in observations
                   if item['kind'] == kind and item['subject'] == claim['subject']]
        if len(matches) != 1:
            return 'UNKNOWN', 'Exactly one current ' + kind + ' observation is required.'
        sources[kind] = matches[0]
    for kind in ('head', 'tree'):
        item = sources[kind]
        if not valid_record(item):
            return 'UNKNOWN', 'Current ' + kind + ' value or binding is invalid.'
        error = evidence_error(item, saved, as_of, max_age)
        if error:
            return 'UNKNOWN', 'Current ' + kind + ': ' + error
    if (observation is not None and observation['kind'] == 'test'
            and observation['subject'] == claim['subject']
            and valid_record(observation)):
        if any(observation['binding'][kind] != sources[kind]['value']
               for kind in ('head', 'tree')):
            return 'STALE', 'Test receipt does not cover the supplied current source.'
    return None


def compare_item(claim, observation, saved, as_of, max_age, observations=()):
    kind = claim['kind']
    if kind == 'test':
        source_error = test_source_error(claim, observation, observations,
                                         saved, as_of, max_age)
        if source_error:
            return source_error
    if not valid_record(claim):
        return 'UNKNOWN', 'Claim value or binding is missing or invalid.'
    if kind == 'action' and claim['value']['outcome'] in ('done', 'uncertain'):
        return 'DO_NOT_REPEAT', HOLD
    if observation is None:
        return 'UNKNOWN', 'No observation was supplied.'
    if observation['kind'] != kind or observation['subject'] != claim['subject']:
        return 'UNKNOWN', 'Observation kind or subject does not match the claim.'
    if not valid_record(observation):
        return 'UNKNOWN', 'Observation value or binding is missing or invalid.'
    value, current = claim['value'], observation['value']
    binding, current_binding = claim['binding'], observation['binding']
    if kind == 'action':
        if binding != current_binding:
            return 'UNKNOWN', 'Operation identity differs. No replay is authorized.'
        if current['outcome'] in ('done', 'uncertain'):
            return 'DO_NOT_REPEAT', HOLD
    error = evidence_error(observation, saved, as_of, max_age)
    if error:
        return 'UNKNOWN', error
    if kind == 'action':
        if value['idempotent'] is not True or current['idempotent'] is not True:
            return 'DO_NOT_REPEAT', HOLD
        return 'MATCH', 'Both assert not_started with matching identity and receipt.'
    if kind == 'test':
        if binding != current_binding:
            return 'STALE', 'Test binding changed. Prior evidence does not cover this state.'
        if current == 'failed':
            return 'DRIFT', 'The supplied current test result is failed.'
        if value != current:
            return 'DRIFT', 'The supplied test results differ.'
    elif kind == 'approval':
        if binding != current_binding:
            return 'STALE', 'Approval does not cover current bytes.'
        if value == 'denied' or current == 'denied':
            return 'DRIFT', 'The supplied approval state includes denied.'
    elif kind == 'capability':
        if binding != current_binding:
            return 'DRIFT', 'Capability operation or model changed.'
        if current == 'failure' or value != current:
            return 'DRIFT', 'The supplied capability result is failure or differs.'
    elif kind == 'process':
        if value['state'] == 'starting' or current['state'] == 'starting':
            return 'UNKNOWN', 'Starting state is unresolved. Wait and observe.'
        if value != current or binding != current_binding:
            return 'DRIFT', 'Explicit process state or identity differs.'
    elif value != current:
        return 'DRIFT', 'The supplied identifiers or digests differ.'
    return 'MATCH', 'Listed values and required bindings match supplied evidence.'


def compare(checkpoint, observed, max_age_seconds=300):
    """Return deterministic advice. Raise InputError for invalid packets."""
    if type(max_age_seconds) is not int or max_age_seconds <= 0:
        raise InputError('Max age must be a positive integer.')
    try:
        json_types(checkpoint)
        json_types(observed)
    except RecursionError:
        raise InputError('Input nesting is too deep.') from None
    diagnostics = []
    claims, saved = packet(checkpoint, 'claims', 'saved_at', '/checkpoint', diagnostics)
    observations, as_of = packet(observed, 'observations', 'as_of', '/observed', diagnostics)
    if as_of < saved:
        raise InputError('As-of time precedes saved time.')
    by_id = {item['id']: item for item in observations}
    claim_ids = {item['id'] for item in claims}
    items = []
    for claim in claims:
        verdict, reason = compare_item(claim, by_id.get(claim['id']), saved,
                                       as_of, max_age_seconds, observations)
        items.append({'id': claim['id'], 'kind': claim['kind'],
                      'verdict': verdict, 'reason': reason})
    for index, observation in enumerate(observations):
        if observation['id'] not in claim_ids:
            diagnostics.append(('/observed/observations/' + str(index),
                                'Observation has no corresponding claim.'))
    for path, reason in sorted(diagnostics):
        items.append({'id': path, 'kind': 'diagnostic', 'verdict': 'UNKNOWN',
                      'reason': reason})
    advice = 'REVIEW_AUTHORIZED_NEXT_STEP'
    if any(item['verdict'] != 'MATCH' for item in items):
        advice = 'REVERIFY_BEFORE_RESUME'
    if any(item['kind'] == 'action' and item['verdict'] == 'DO_NOT_REPEAT' for item in items):
        advice = 'STOP_AND_VERIFY_OUTCOME'
    return {'schema_version': 1, 'as_of': observed['as_of'], 'items': items,
            'advice': advice, 'notice': NOTICE}


def pairs_hook(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError('Duplicate JSON object key.')
        result[key] = value
    return result


def reject_constant(value):
    raise InputError('Non-JSON numeric constant.')


def read_packet(path):
    try:
        nonblock = getattr(os, 'O_NONBLOCK', 0)
        if not nonblock and not stat.S_ISREG(os.stat(path).st_mode):
            raise InputError('Input must be a regular file.')
        flags = os.O_RDONLY | nonblock | getattr(os, 'O_BINARY', 0)
        descriptor = os.open(path, flags)
        try:
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise InputError('Input must be a regular file.')
            chunks = []
            remaining = LIMIT + 1
            while remaining:
                chunk = os.read(descriptor, min(remaining, 65536))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            data = b''.join(chunks)
        finally:
            os.close(descriptor)
        if len(data) > LIMIT:
            raise InputError('Input file exceeds 1 MiB.')
        return json.loads(data.decode('utf-8'), object_pairs_hook=pairs_hook,
                          parse_constant=reject_constant)
    except (OSError, UnicodeError):
        raise InputError('Cannot read input as UTF-8 JSON.') from None
    except InputError:
        raise
    except (ValueError, RecursionError):
        raise InputError('Malformed JSON input.') from None


def markdown(report):
    lines = ['Advice: ' + report['advice'], 'As of: ' + report['as_of'], '']
    for item in report['items']:
        # JSON quoting prevents untrusted identifiers from injecting Markdown lines.
        label = json.dumps(item['id'], ensure_ascii=True)
        label = re.sub(r'([\\`*_{}\[\]()<>#!|])', r'\\\1', label)
        lines.append('- ' + label + ': ' + item['verdict'] + '. ' + item['reason'])
    return '\n'.join(lines + ['', report['notice']])


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise InputError('Invalid command usage.')


def main(argv=None):
    parser = Parser(description='Compare supplied task claims and observations.')
    parser.add_argument('checkpoint')
    parser.add_argument('observed')
    parser.add_argument('--format', choices=('json', 'md'), default='json')
    parser.add_argument('--max-age-seconds', type=int, default=300)
    try:
        args = parser.parse_args(argv)
        if args.max_age_seconds <= 0:
            raise InputError('Max age must be a positive integer.')
        report = compare(read_packet(args.checkpoint), read_packet(args.observed),
                         args.max_age_seconds)
        output = (json.dumps(report, ensure_ascii=True, indent=2, allow_nan=False)
                  if args.format == 'json' else markdown(report))
        print(output)
        return 0 if all(item['verdict'] == 'MATCH' for item in report['items']) else 1
    except InputError as error:
        print('Error: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
