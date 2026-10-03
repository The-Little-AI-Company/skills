"""Structural regression tests; no statechart interpretation or proof."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'check_inventory.py'
spec = importlib.util.spec_from_file_location('inventory', SCRIPT)
inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory)
BASE = json.loads((ROOT / 'examples' / 'minimal-inventory.json').read_text())


class InventoryTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(inventory.check(BASE), ([], []))

    def test_invalid_structures(self):
        changes = {
            'duplicate state': lambda x: x['states'].append(copy.deepcopy(x['states'][1])),
            'bad parent': lambda x: x['states'][1].update(parent='Missing'),
            'cycle': lambda x: x['states'][0].update(parent='Busy'),
            'bad initial': lambda x: x['states'][0].update(initial='Missing'),
            'bad transition': lambda x: x['transitions'][0].update(target='Missing'),
            'bad event': lambda x: x['transitions'][0].update(event='MISSING'),
            'bad kind': lambda x: x['states'][1].update(kind='unknown'),
            'bad guard': lambda x: x['transitions'][0].update(guard=[]),
            'invalid parallel': lambda x: x['states'][1].update(kind='parallel'),
            'invalid event shape': lambda x: x['events'].append({}),
        }
        for name, change in changes.items():
            with self.subTest(name=name):
                model = copy.deepcopy(BASE)
                change(model)
                self.assertTrue(inventory.check(model)[0])

    def test_overlap_warning(self):
        model = copy.deepcopy(BASE)
        model['transitions'].append({'id': 'other', 'source': 'Idle', 'event': 'START', 'target': 'Idle', 'guard': 'ready'})
        self.assertEqual(len(inventory.check(model)[1]), 1)

    def test_cli_success(self):
        result = subprocess.run([sys.executable, str(SCRIPT), str(ROOT / 'examples' / 'minimal-inventory.json')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_cli_malformed(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'bad.json'
            source.write_text('not json')
            result = subprocess.run([sys.executable, str(SCRIPT), str(source)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)


if __name__ == '__main__':
    unittest.main()
