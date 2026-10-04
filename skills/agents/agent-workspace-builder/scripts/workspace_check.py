#!/usr/bin/env python3
"""Advisory structural checks on a supplied snapshot; no live verification or authority."""
import argparse
from collections import deque
import json
from pathlib import Path
import sys

STATES = {'backlog', 'ready', 'running', 'waiting_external', 'blocked', 'paused', 'cancel_requested', 'review', 'done', 'canceled'}

def validate(data):
    issues = []
    if not isinstance(data, dict) or data.get('schema_version') != 1:
        return ['Expected a schema_version 1 object.']
    collections = {}
    for kind in ('capabilities', 'tasks'):
        items = data.get(kind)
        if not isinstance(items, list) or len(items) > 500:
            return [f'{kind} must be a list of at most 500 records.']
        records = {}
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get('id'), str) or not item['id'].strip():
                issues.append(f'{kind}: record needs a nonempty string id.')
                continue
            if item['id'] in records:
                issues.append(f'{kind}: duplicate id {item["id"]}.')
            records[item['id']] = item
        collections[kind] = records
    caps, tasks = collections['capabilities'], collections['tasks']
    for cid, cap in caps.items():
        for flag in ('implemented', 'configured', 'verified'):
            if type(cap.get(flag)) is not bool:
                issues.append(f'{cid}: {flag} must be boolean.')
        if cap.get('implemented') and not cap.get('tool_binding'):
            issues.append(f'{cid}: implemented capability lacks a tool binding.')
        if cap.get('verified') and not (cap.get('implemented') and cap.get('configured') and cap.get('evidence')):
            issues.append(f'{cid}: verified claim lacks implementation, configuration, or evidence.')
    edges = {tid: [] for tid in tasks}
    indegree = {tid: 0 for tid in tasks}
    for tid, task in tasks.items():
        state = task.get('state')
        if state not in STATES:
            issues.append(f'{tid}: unknown state.')
        deps = task.get('dependencies', [])
        if not isinstance(deps, list) or any(not isinstance(x, str) for x in deps):
            issues.append(f'{tid}: dependencies must be string IDs.')
            deps = []
        for dep in set(deps):
            if dep not in tasks:
                issues.append(f'{tid}: missing dependency {dep}.')
            else:
                edges[dep].append(tid)
                indegree[tid] += 1
                if state in ('ready', 'running', 'waiting_external', 'review', 'done') and tasks[dep].get('state') != 'done':
                    issues.append(f'{tid}: dependency {dep} is not done.')
        required = task.get('capabilities', [])
        if not isinstance(required, list) or any(not isinstance(x, str) for x in required):
            issues.append(f'{tid}: capabilities must be string IDs.')
            required = []
        for cid in required:
            if cid not in caps:
                issues.append(f'{tid}: unknown capability {cid}.')
            elif state in ('ready', 'running', 'waiting_external') and not (caps[cid].get('implemented') and caps[cid].get('configured')):
                issues.append(f'{tid}: capability {cid} is unavailable.')
        if state == 'blocked' and not task.get('blocker'):
            issues.append(f'{tid}: blocked task needs a reason.')
        if state == 'running' and not (task.get('attempt_id') and task.get('worker_id')):
            issues.append(f'{tid}: running task needs attempt and worker IDs.')
        if state == 'waiting_external' and not (task.get('attempt_id') and task.get('provider_request_id')):
            issues.append(f'{tid}: external wait needs attempt and provider request IDs.')
        if state == 'done' and not (task.get('evidence') and (task.get('artifacts') or task.get('effect_receipt'))):
            issues.append(f'{tid}: done claim needs evidence and an artifact or effect receipt.')
        if state == 'canceled' and task.get('outstanding_external_jobs'):
            issues.append(f'{tid}: canceled claim has outstanding external work.')
    queue = deque(tid for tid, n in indegree.items() if n == 0)
    seen = 0
    while queue:
        tid = queue.popleft()
        seen += 1
        for child in edges[tid]:
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    if seen != len(tasks):
        issues.append('Task dependencies contain a cycle.')
    return issues

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot')
    args = parser.parse_args()
    try:
        path = Path(args.snapshot)
        if not path.is_file() or path.is_symlink():
            raise ValueError('Supply a local regular JSON file, not a symlink.')
        with path.open('rb') as stream:
            raw = stream.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise ValueError('Snapshot exceeds 2 MiB.')
        issues = validate(json.loads(raw))
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({'error': str(exc), 'advisory_only': True}))
        return 2
    print(json.dumps({'issues': issues, 'advisory_only': True, 'live_verified': False}, indent=2))
    return 1 if issues else 0

if __name__ == '__main__':
    sys.exit(main())
