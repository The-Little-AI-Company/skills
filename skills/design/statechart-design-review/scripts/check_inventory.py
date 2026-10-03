#!/usr/bin/env python3
"""Structural inventory lint only; not a statechart interpreter or proof tool."""
import json
import sys
from collections import Counter, defaultdict


def check(model):
    errors, warnings = [], []
    if not isinstance(model, dict):
        return ['top level must be an object'], []
    states, events, transitions = (model.get(k) for k in ('states', 'events', 'transitions'))
    if not all(isinstance(v, list) for v in (states, events, transitions)):
        return ['states, events, and transitions must be arrays'], []
    if not all(isinstance(s, dict) and isinstance(s.get('id'), str) and s['id'] for s in states):
        return ['every state needs a nonempty string id'], []
    if not all(isinstance(e, str) and e for e in events):
        return ['events must be nonempty strings'], []
    if not all(isinstance(t, dict) and isinstance(t.get('id'), str) and t['id'] for t in transitions):
        return ['every transition needs a nonempty string id'], []
    for label, ids in [('state', [s['id'] for s in states]), ('event', events), ('transition', [t['id'] for t in transitions])]:
        errors.extend(f'duplicate {label}: {k}' for k, n in Counter(ids).items() if n > 1)
    index = {s['id']: s for s in states}
    children = defaultdict(list)
    roots = []
    for s in states:
        sid, parent = s['id'], s.get('parent')
        if parent is None:
            roots.append(sid)
        elif not isinstance(parent, str) or parent not in index:
            errors.append(f'{sid}: unknown/invalid parent')
        else:
            children[parent].append(sid)
        if s.get('kind') not in ('atomic', 'compound', 'parallel', 'final'):
            errors.append(f'{sid}: invalid kind')
    if len(roots) != 1:
        errors.append('exactly one root is required')
    for s in states:
        sid, kind = s['id'], s.get('kind')
        if kind == 'compound' and s.get('initial') not in children[sid]:
            errors.append(f'{sid}: initial must name a direct child')
        if kind == 'parallel' and (len(children[sid]) < 2 or s.get('initial') is not None):
            errors.append(f'{sid}: parallel needs at least two children and no initial')
        if kind in ('atomic', 'final') and (children[sid] or s.get('initial') is not None):
            errors.append(f'{sid}: leaf cannot have children or initial')
        seen, current = set(), sid
        while isinstance(current, str) and current in index:
            if current in seen:
                errors.append(f'{sid}: parent cycle')
                break
            seen.add(current)
            current = index[current].get('parent')
    groups = defaultdict(list)
    for t in transitions:
        tid = t['id']
        for field in ('source', 'target'):
            value = t.get(field)
            if field == 'target' and value is None:
                continue
            if not isinstance(value, str) or value not in index:
                errors.append(f'{tid}: unknown/invalid {field}')
        event = t.get('event')
        if event is not None and (not isinstance(event, str) or event not in events):
            errors.append(f'{tid}: unknown/invalid event')
        if 'guard' in t and not isinstance(t['guard'], str):
            errors.append(f'{tid}: guard must be descriptive text')
        if isinstance(t.get('source'), str) and (event is None or isinstance(event, str)):
            groups[(t['source'], event)].append(tid)
    for (source, event), ids in groups.items():
        if len(ids) > 1:
            warnings.append(f'{source}/{event}: review guard overlap and priority: {", ".join(ids)}')
    return sorted(set(errors)), sorted(warnings)


def main():
    if len(sys.argv) != 2:
        print('Usage: check_inventory.py inventory.json', file=sys.stderr)
        return 1
    try:
        with open(sys.argv[1], encoding='utf-8') as stream:
            model = json.load(stream)
        errors, warnings = check(model)
    except (OSError, ValueError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1
    for item in errors:
        print(f'ERROR: {item}')
    for item in warnings:
        print(f'WARNING: {item}')
    if not errors:
        print('Structural inventory checks passed; behavior and determinism are not verified.')
    return int(bool(errors))


if __name__ == '__main__':
    sys.exit(main())
