"""Regression cases for independent review findings P2 and P3."""
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_drift_check import drift, SCRIPT

HEAD_A, HEAD_B = 'a' * 40, 'b' * 40
TREE_A, TREE_B = 'c' * 64, 'd' * 64


def packets(saved_tree=TREE_A, current_tree=TREE_A, receipt_tree=TREE_A):
    claims = [
        {'id': 'head', 'kind': 'head', 'subject': 'scope-a', 'value': HEAD_A, 'binding': {}},
        {'id': 'tree', 'kind': 'tree', 'subject': 'scope-a', 'value': saved_tree, 'binding': {}},
        {'id': 'test', 'kind': 'test', 'subject': 'scope-a', 'value': 'passed',
         'binding': {'head': HEAD_A, 'tree': receipt_tree, 'command': 'python check.py'}},
    ]
    observations = copy.deepcopy(claims)
    observations[1]['value'] = current_tree
    for item in observations:
        item.update(source='synthetic fixture', evidence='receipt', observed_at='2026-01-01T12:01:00Z')
    return ({'schema_version': 1, 'saved_at': '2026-01-01T12:00:00Z', 'claims': claims},
            {'schema_version': 1, 'as_of': '2026-01-01T12:02:00Z', 'observations': observations})


def test_verdict(cp, ob):
    return next(row['verdict'] for row in drift.compare(cp, ob)['items'] if row['id'] == 'test')


class ReviewFindings(unittest.TestCase):
    def test_changed_current_tree_invalidates_unchanged_test_receipt(self):
        cp, ob = packets(current_tree=TREE_B)
        self.assertEqual(test_verdict(cp, ob), 'STALE')

    def test_two_matching_old_receipts_cannot_cover_current_bytes(self):
        cp, ob = packets(saved_tree=TREE_B, current_tree=TREE_B)
        self.assertEqual(test_verdict(cp, ob), 'STALE')
        self.assertEqual(drift.compare(cp, ob)['advice'], 'REVERIFY_BEFORE_RESUME')

    def test_matching_current_receipt_is_control(self):
        cp, ob = packets(saved_tree=TREE_B, current_tree=TREE_B, receipt_tree=TREE_B)
        self.assertEqual(test_verdict(cp, ob), 'MATCH')

    def test_current_head_invalidates_old_receipt(self):
        cp, ob = packets()
        cp['claims'][0]['value'] = ob['observations'][0]['value'] = HEAD_B
        self.assertEqual(test_verdict(cp, ob), 'STALE')

    def test_source_scope_is_exact_and_unrelated_changes_stay_independent(self):
        cp, ob = packets()
        for kind, value in [('head', HEAD_B), ('tree', TREE_B)]:
            other = {'id': 'other-' + kind, 'kind': kind, 'subject': 'scope-b', 'value': value, 'binding': {}}
            cp['claims'].append(copy.deepcopy(other))
            other.update(source='other scope', evidence='metadata', observed_at='2026-01-01T12:01:00Z')
            ob['observations'].append(other)
        self.assertEqual(test_verdict(cp, ob), 'MATCH')
        ob['observations'][1]['subject'] = 'Scope-a'
        self.assertEqual(test_verdict(cp, ob), 'UNKNOWN')

    def test_test_only_packet_has_no_current_source_proof(self):
        cp, ob = packets()
        cp['claims'] = cp['claims'][2:]
        ob['observations'] = ob['observations'][2:]
        self.assertEqual(test_verdict(cp, ob), 'UNKNOWN')

    def test_each_current_source_dimension_is_required(self):
        for kind in ['head', 'tree']:
            with self.subTest(kind=kind):
                cp, ob = packets()
                ob['observations'] = [item for item in ob['observations'] if item['kind'] != kind]
                self.assertEqual(test_verdict(cp, ob), 'UNKNOWN')

    def test_ambiguous_source_is_unknown_even_if_identical(self):
        for value in [TREE_A, TREE_B]:
            with self.subTest(value=value):
                cp, ob = packets()
                extra = copy.deepcopy(ob['observations'][1])
                extra.update(id='second-tree', value=value)
                ob['observations'].append(extra)
                self.assertEqual(test_verdict(cp, ob), 'UNKNOWN')

    def test_bad_source_observation_cannot_support_test_match(self):
        changes = [{'observed_at': '2026-01-01T11:59:59Z'}, {'observed_at': '2026-01-01T12:03:00Z'},
                   {'value': 'not-a-digest'}, {'binding': {'unexpected': True}}, {'source': ''}]
        for change in changes:
            with self.subTest(change=change):
                cp, ob = packets()
                ob['observations'][1].update(change)
                self.assertEqual(test_verdict(cp, ob), 'UNKNOWN')

    def test_both_review_cli_reproductions_are_nonzero(self):
        for saved_tree in [TREE_A, TREE_B]:
            with self.subTest(saved_tree=saved_tree), tempfile.TemporaryDirectory() as tmp:
                cp, ob = packets(saved_tree=saved_tree, current_tree=TREE_B)
                cp['claims'] = cp['claims'][1:]
                ob['observations'] = ob['observations'][1:]
                c, o = Path(tmp) / 'c.json', Path(tmp) / 'o.json'
                c.write_text(json.dumps(cp), encoding='utf-8')
                o.write_text(json.dumps(ob), encoding='utf-8')
                run = subprocess.run([sys.executable, '-B', str(SCRIPT), str(c), str(o)], capture_output=True, text=True, timeout=3)
                self.assertEqual(run.returncode, 1)
                row = next(x for x in json.loads(run.stdout)['items'] if x['id'] == 'test')
                self.assertIn(row['verdict'], ['STALE', 'UNKNOWN'])

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'FIFO test requires POSIX')
    def test_fifo_rejected_promptly_without_leaked_child(self):
        with tempfile.TemporaryDirectory() as tmp:
            fifo, observed = Path(tmp) / 'checkpoint.json', Path(tmp) / 'observed.json'
            os.mkfifo(fifo)
            observed.write_text('{}', encoding='utf-8')
            child = subprocess.Popen([sys.executable, '-B', str(SCRIPT), str(fifo), str(observed)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                try:
                    stdout, stderr = child.communicate(timeout=1.5)
                except subprocess.TimeoutExpired:
                    self.fail('FIFO input blocked longer than 1.5 seconds')
                self.assertEqual(child.returncode, 2)
                self.assertNotIn('Traceback', stderr)
                self.assertEqual(stdout, '')
            finally:
                if child.poll() is None:
                    child.kill()
                child.communicate(timeout=3)
                self.assertIsNotNone(child.poll())

    def test_directory_input_is_clean_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(drift.InputError):
                drift.read_packet(tmp)

    def test_stale_failed_receipt_precedes_failed_result(self):
        cp, ob = packets(saved_tree=TREE_B, current_tree=TREE_B)
        ob['observations'][2]['value'] = 'failed'
        self.assertEqual(test_verdict(cp, ob), 'STALE')

    def test_ambiguous_dimension_precedes_other_dimension_mismatch(self):
        cp, ob = packets(saved_tree=TREE_B, current_tree=TREE_B)
        other = copy.deepcopy(ob['observations'][0])
        other['id'] = 'duplicate-head'
        ob['observations'].append(other)
        self.assertEqual(test_verdict(cp, ob), 'UNKNOWN')

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'FIFO symlink test requires POSIX')
    def test_symlink_to_fifo_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            fifo, link = Path(tmp) / 'pipe', Path(tmp) / 'link.json'
            os.mkfifo(fifo)
            link.symlink_to(fifo)
            run = subprocess.run([sys.executable, '-B', str(SCRIPT), str(link), str(link)],
                                 capture_output=True, text=True, timeout=1.5)
            self.assertEqual(run.returncode, 2)
            self.assertNotIn('Traceback', run.stderr)

    def test_regular_file_byte_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'packet.json'
            path.write_bytes(b'{}' + b' ' * (drift.LIMIT - 2))
            self.assertEqual(drift.read_packet(path), {})
            path.write_bytes(b'{}' + b' ' * (drift.LIMIT - 1))
            with self.assertRaises(drift.InputError):
                drift.read_packet(path)


if __name__ == '__main__':
    unittest.main()
