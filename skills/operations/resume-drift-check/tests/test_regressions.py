"""Held-out synthetic variations authored after the first comparator was frozen."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / 'tests'))
from test_drift_check import packets, drift, A, TREE, SCRIPT


class HeldOut(unittest.TestCase):
    def test_changed_command_same_source(self):
        cp, ob = packets('test', 'passed', {'head': A, 'tree': TREE, 'command': 'python one.py'})
        ob['observations'][0]['binding']['command'] = 'python two.py'
        self.assertEqual(drift.compare(cp, ob)['items'][0]['verdict'], 'STALE')

    def test_bool_is_not_process_identity(self):
        cp, ob = packets('process', {'state': 'running'}, {'pid': 42, 'start_token': 't', 'owner': 'demo'})
        ob['observations'][0]['binding']['pid'] = True
        self.assertEqual(drift.compare(cp, ob)['items'][0]['verdict'], 'UNKNOWN')

    def test_completed_different_subject_is_not_my_completion(self):
        cp, ob = packets('action', {'outcome': 'not_started', 'idempotent': True}, {'operation_id': 'demo'})
        ob['observations'][0]['subject'] = 'different-task'
        ob['observations'][0]['value']['outcome'] = 'done'
        self.assertEqual(drift.compare(cp, ob)['items'][0]['verdict'], 'UNKNOWN')

    def test_nested_unknown_binding_is_reported(self):
        cp, ob = packets()
        ob['observations'][0]['binding']['unexpected'] = {'nested': 'value'}
        result = drift.compare(cp, ob)
        self.assertEqual(result['items'][0]['verdict'], 'UNKNOWN')
        self.assertTrue(any(x['kind'] == 'diagnostic' for x in result['items']))

    def test_duplicate_observation_rejected(self):
        cp, ob = packets()
        ob['observations'].append(copy.deepcopy(ob['observations'][0]))
        with self.assertRaises(drift.InputError):
            drift.compare(cp, ob)

    def test_exact_age_boundary_and_one_microsecond_later(self):
        cp, ob = packets()
        ob['as_of'] = '2026-01-01T12:06:00Z'
        self.assertEqual(drift.compare(cp, ob)['items'][0]['verdict'], 'MATCH')
        ob['as_of'] = '2026-01-01T12:06:00.000001Z'
        self.assertEqual(drift.compare(cp, ob)['items'][0]['verdict'], 'UNKNOWN')

    def test_json_integer_limit_is_clean_input_error(self):
        cp, ob = packets()
        with tempfile.TemporaryDirectory() as tmp:
            c, o = Path(tmp) / 'c.json', Path(tmp) / 'o.json'
            c.write_text('{"untrusted_number":' + '9' * 5000 + '}')
            o.write_text(json.dumps(ob))
            run = subprocess.run([sys.executable, '-B', str(SCRIPT), str(c), str(o)],
                                 capture_output=True, text=True, timeout=10)
            self.assertEqual(run.returncode, 2)
            self.assertNotIn('Traceback', run.stderr)

    def test_two_independent_mismatches(self):
        cp, ob = packets('approval', 'granted', {'artifact_sha256': TREE})
        ob['observations'][0]['binding']['artifact_sha256'] = 'd' * 64
        c2, o2 = packets('capability', 'success', {'operation': 'hello', 'model': 'model-one'})
        c2['claims'][0]['id'] = 'second'
        o2['observations'][0]['id'] = 'second'
        o2['observations'][0]['binding']['model'] = 'model-two'
        cp['claims'] += c2['claims']
        ob['observations'] += o2['observations']
        result = drift.compare(cp, ob)
        self.assertEqual([x['verdict'] for x in result['items']], ['STALE', 'DRIFT'])
        self.assertEqual(result['advice'], 'REVERIFY_BEFORE_RESUME')


if __name__ == '__main__':
    unittest.main(verbosity=2)

