#!/usr/bin/env python3
"""Offline structural checks, not runtime parity certification."""
import json,re,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];errors=[]
for p in root.rglob('*.md'):
 for dest in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' in dest or dest.startswith('#'):continue
  path=(p.parent/dest.split('#')[0]).resolve()
  if not path.is_relative_to(root) or not path.is_file():errors.append(f'Broken/escaping reference: {p.name}: {dest}')
cat=json.loads((root/'assets/capabilities.json').read_text());items=cat['capabilities']
ids=[x['id'] for x in items]
if len(ids)!=len(set(ids)):errors.append('Duplicate capability IDs')
for item in items:
 for k in ['id','name','source_url','manus_usage','workspace_route','acceptance','guide','status']:
  if not item.get(k):errors.append(f'Missing {k}: {item.get("id")}')
 if not (root/item['guide']).is_file():errors.append(f'Missing guide {item["guide"]}')
 if item['live_verified']:errors.append('Bundled baseline must not preclaim live verification')
contract=json.loads((root/'assets/run-contract.example.json').read_text())
if not set(contract['capabilities']).issubset(ids):errors.append('Unknown capability in example contract')
timeline=json.loads((root/'assets/timeline.example.json').read_text())
assets={x['id'] for x in timeline['assets']}
for t in timeline['tracks']:
 for x in t['items']:
  if x.get('asset_id') not in assets:errors.append('Unknown timeline asset')
  if x['start_frame']<0 or x['duration_frames']<=0 or x['start_frame']+x['duration_frames']>timeline['duration_frames']:errors.append('Invalid timeline timing')
print(json.dumps({'capabilities':len(items),'structural_errors':errors,'live_verified':False},indent=2))
sys.exit(bool(errors))
