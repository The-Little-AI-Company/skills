"""Write the synthetic demonstration packets in the current directory."""
import json
from pathlib import Path

cases = json.loads(Path(__file__).with_name('cases.json').read_text(encoding='utf-8'))
case = next(item for item in cases['cases'] if item['name'] == 'combined-demo')
targets = [Path('checkpoint.json'), Path('observed.json')]
if any(path.exists() for path in targets):
    raise SystemExit('Example input already exists. Use a fresh directory or inspect it first.')
for path, key in zip(targets, ['checkpoint', 'observed']):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(case[key], stream, indent=2)
        stream.write('\n')
print('Created synthetic checkpoint.json and observed.json. Comparator exit 1 is expected.')
