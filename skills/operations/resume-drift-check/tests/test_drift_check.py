"""Synthetic contract tests. These do not measure agent decision quality."""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/drift_check.py'
spec = importlib.util.spec_from_file_location('drift_check', SCRIPT)
drift = importlib.util.module_from_spec(spec)
spec.loader.exec_module(drift)
A, B, TREE = 'a' * 40, 'b' * 40, 'c' * 64


def packets(kind='head', value=A, binding=None):
    claim = {'id': 'sample', 'kind': kind, 'subject': 'synthetic-task',
             'value': copy.deepcopy(value), 'binding': copy.deepcopy(binding or {})}
    observation = copy.deepcopy(claim)
    observation.update(source='synthetic receipt', evidence='receipt',
                       observed_at='2026-01-01T12:01:00Z')
    claims, observations = [claim], [observation]
    if kind == 'test':
        for source_kind in ('head', 'tree'):
            source = {'id': 'current-' + source_kind, 'kind': source_kind,
                      'subject': claim['subject'], 'value': binding[source_kind], 'binding': {}}
            claims.append(copy.deepcopy(source))
            source.update(source='synthetic current source', evidence='metadata',
                          observed_at='2026-01-01T12:01:00Z')
            observations.append(source)
    return ({'schema_version': 1, 'saved_at': '2026-01-01T12:00:00Z', 'claims': claims},
            {'schema_version': 1, 'as_of': '2026-01-01T12:02:00Z',
             'observations': observations})


class ContractTests(unittest.TestCase):
    def verdict(self, cp, ob):
        return drift.compare(cp, ob)['items'][0]['verdict']

    def test_corrected_controls(self):
        controls = [
            ('head', A, {}), ('tree', TREE, {}),
            ('test', 'passed', {'head': A, 'tree': TREE, 'command': 'python check.py'}),
            ('action', {'outcome': 'not_started', 'idempotent': True}, {'operation_id': 'sample-op'}),
            ('process', {'state': 'running'}, {'pid': 42, 'start_token': 'start-one', 'owner': 'sample-owner'}),
            ('process', {'state': 'missing'}, {}),
            ('approval', 'granted', {'artifact_sha256': TREE}),
            ('capability', 'success', {'operation': 'hello', 'model': 'sample-model'}),
        ]
        for kind, value, binding in controls:
            with self.subTest(kind=kind, value=value):
                cp, ob = packets(kind, value, binding)
                self.assertEqual(self.verdict(cp, ob), 'MATCH')
                self.assertEqual(drift.compare(cp, ob)['advice'], 'REVIEW_AUTHORIZED_NEXT_STEP')

    def test_changed_head(self):
        cp, ob = packets()
        ob['observations'][0]['value'] = B
        self.assertEqual(self.verdict(cp, ob), 'DRIFT')

    def test_changed_dirty_bytes(self):
        cp, ob = packets('tree', TREE)
        ob['observations'][0]['value'] = 'd' * 64
        self.assertEqual(self.verdict(cp, ob), 'DRIFT')

    def test_same_head_changed_tested_bytes(self):
        cp, ob = packets('test', 'passed', {'head': A, 'tree': TREE, 'command': 'python check.py'})
        ob['observations'][0]['binding']['tree'] = 'd' * 64
        self.assertEqual(self.verdict(cp, ob), 'STALE')

    def test_changed_test_head(self):
        cp, ob = packets('test', 'passed', {'head': A, 'tree': TREE, 'command': 'python check.py'})
        ob['observations'][0]['binding']['head'] = B
        self.assertEqual(self.verdict(cp, ob), 'STALE')

    def test_failed_test_cannot_match(self):
        cp, ob = packets('test', 'failed', {'head': A, 'tree': TREE, 'command': 'python check.py'})
        self.assertEqual(self.verdict(cp, ob), 'DRIFT')

    def test_action_done_or_uncertain_holds_without_evidence(self):
        for outcome in ['done', 'uncertain']:
            with self.subTest(outcome=outcome):
                cp, ob = packets('action', {'outcome': outcome, 'idempotent': False}, {'operation_id': 'sample-op'})
                ob['observations'] = []
                result = drift.compare(cp, ob)
                self.assertEqual(result['items'][0]['verdict'], 'DO_NOT_REPEAT')
                self.assertEqual(result['advice'], 'STOP_AND_VERIFY_OUTCOME')
                self.assertIn('not proof', result['items'][0]['reason'])

    def test_non_idempotent_action_on_hold(self):
        cp, ob = packets('action', {'outcome': 'not_started', 'idempotent': False}, {'operation_id': 'sample-op'})
        self.assertEqual(self.verdict(cp, ob), 'DO_NOT_REPEAT')

    def test_changed_operation_is_not_a_match(self):
        cp, ob = packets('action', {'outcome': 'not_started', 'idempotent': True}, {'operation_id': 'sample-op'})
        ob['observations'][0]['binding']['operation_id'] = 'different-op'
        self.assertEqual(self.verdict(cp, ob), 'UNKNOWN')

    def test_missing_process(self):
        cp, ob = packets('process', {'state': 'running'}, {'pid': 42, 'start_token': 'start-one', 'owner': 'sample-owner'})
        ob['observations'][0].update(value={'state': 'missing'}, binding={})
        self.assertEqual(self.verdict(cp, ob), 'DRIFT')

    def test_starting_process_is_unresolved(self):
        cp, ob = packets('process', {'state': 'running'}, {'pid': 42, 'start_token': 'start-one', 'owner': 'sample-owner'})
        ob['observations'][0]['value']['state'] = 'starting'
        self.assertEqual(self.verdict(cp, ob), 'UNKNOWN')

    def test_reused_pid_is_drift(self):
        cp, ob = packets('process', {'state': 'running'}, {'pid': 42, 'start_token': 'start-one', 'owner': 'sample-owner'})
        ob['observations'][0]['binding']['start_token'] = 'start-two'
        self.assertEqual(self.verdict(cp, ob), 'DRIFT')

    def test_approval_covers_exact_bytes(self):
        cp, ob = packets('approval', 'granted', {'artifact_sha256': TREE})
        ob['observations'][0]['binding']['artifact_sha256'] = 'd' * 64
        self.assertEqual(self.verdict(cp, ob), 'STALE')

    def test_metadata_does_not_prove_a_call(self):
        cp, ob = packets('capability', 'success', {'operation': 'hello', 'model': 'sample-model'})
        ob['observations'][0]['evidence'] = 'metadata'
        self.assertEqual(self.verdict(cp, ob), 'UNKNOWN')

    def test_missing_observation_fields_never_match(self):
        for field in ['value', 'binding', 'source', 'observed_at', 'evidence']:
            with self.subTest(field=field):
                cp, ob = packets()
                del ob['observations'][0][field]
                self.assertEqual(self.verdict(cp, ob), 'UNKNOWN')

    def test_missing_test_tree_binding_is_unknown(self):
        cp, ob = packets('test', 'passed', {'head': A, 'tree': TREE, 'command': 'python check.py'})
        del ob['observations'][0]['binding']['tree']
        self.assertEqual(self.verdict(cp, ob), 'UNKNOWN')

    def test_wrong_subject(self):
        cp, ob = packets()
        ob['observations'][0]['subject'] = 'other-task'
        self.assertEqual(self.verdict(cp, ob), 'UNKNOWN')

    def test_invalid_action_enum(self):
        cp, ob = packets('action', {'outcome': 'uncertain', 'idempotent': None}, {'operation_id': 'sample-op'})
        cp['claims'][0]['value']['outcome'] = 'partly_applied'
        self.assertEqual(self.verdict(cp, ob), 'UNKNOWN')

    def test_missing_all_observations(self):
        cp, ob = packets()
        ob['observations'] = []
        self.assertEqual(self.verdict(cp, ob), 'UNKNOWN')

    def test_time_consistency(self):
        for stamp in ['2026-01-01T11:59:59Z', '2026-01-01T12:03:00Z', 'bad-time']:
            with self.subTest(stamp=stamp):
                cp, ob = packets()
                ob['observations'][0]['observed_at'] = stamp
                self.assertEqual(self.verdict(cp, ob), 'UNKNOWN')
        cp, ob = packets()
        ob['as_of'] = '2026-01-01T12:10:00Z'
        self.assertEqual(self.verdict(cp, ob), 'UNKNOWN')

    def test_unknown_fields_and_extra_observations_are_visible(self):
        cp, ob = packets()
        ob['surprise'] = True
        extra = copy.deepcopy(ob['observations'][0])
        extra['id'] = 'unclaimed'
        ob['observations'].append(extra)
        report = drift.compare(cp, ob)
        self.assertEqual(sum(x['verdict'] == 'UNKNOWN' for x in report['items']), 2)
        self.assertEqual(report['advice'], 'REVERIFY_BEFORE_RESUME')

    def test_invalid_packet_contracts(self):
        mutations = [lambda p: p.update(schema_version=2),
                     lambda p: p.update(claims=[]),
                     lambda p: p['claims'].append(copy.deepcopy(p['claims'][0])),
                     lambda p: p['claims'][0].update(kind='branch'),
                     lambda p: p['claims'][0].update(subject='')]
        for change in mutations:
            cp, ob = packets()
            change(cp)
            with self.assertRaises(drift.InputError):
                drift.compare(cp, ob)

    def test_deterministic_report(self):
        cp, ob = packets()
        self.assertEqual(json.dumps(drift.compare(cp, ob)), json.dumps(drift.compare(cp, ob)))

    def test_example_cases(self):
        cases = json.loads((ROOT / 'examples/cases.json').read_text())
        self.assertTrue(cases['synthetic'])
        for case in cases['cases']:
            with self.subTest(name=case['name']):
                result = drift.compare(case['checkpoint'], case['observed'])
                actual = {x['id']: x['verdict'] for x in result['items']}
                self.assertEqual(actual, case['expected_verdicts'])
                self.assertEqual(result['advice'], case['expected_advice'])

    def test_cli_contract(self):
        cp, ob = packets()
        with tempfile.TemporaryDirectory() as tmp:
            c, o = Path(tmp) / 'checkpoint.json', Path(tmp) / 'observed.json'
            c.write_text(json.dumps(cp))
            o.write_text(json.dumps(ob))
            def run(*args):
                return subprocess.run([sys.executable, '-B', str(SCRIPT), str(c), str(o), *args],
                                      capture_output=True, text=True, timeout=10)
            good = run()
            self.assertEqual(good.returncode, 0)
            self.assertIn('does not authorize', json.loads(good.stdout)['notice'])
            md = run('--format', 'md')
            self.assertEqual(md.returncode, 0)
            self.assertGreater(len(md.stdout.splitlines()), 3)
            ob['observations'][0]['value'] = B
            o.write_text(json.dumps(ob))
            self.assertEqual(run().returncode, 1)
            for invalid in ['{', '{"schema_version":1,"schema_version":1}', '{"x":NaN}', 'x' * (1024 * 1024 + 1)]:
                c.write_text(invalid)
                bad = run()
                self.assertEqual(bad.returncode, 2)
                self.assertNotIn('Traceback', bad.stderr)
            c.write_text(json.dumps(cp))
            self.assertEqual(run('--max-age-seconds', '0').returncode, 2)


if __name__ == '__main__':
    unittest.main()
