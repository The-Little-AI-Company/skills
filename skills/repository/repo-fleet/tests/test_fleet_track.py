import contextlib
import io
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import fleet_track

HEADER = list(fleet_track.COLUMNS)
URL = "https://github.com/owner/{}/pull/1"
GOOD = [{"__typename": "CheckRun", "status": "COMPLETED", "conclusion": "SUCCESS"}]
BAD = [{"__typename": "CheckRun", "status": "COMPLETED", "conclusion": "FAILURE"}]


def row(repo, ring="10", pr=True, state="open", **over):
    base = {"repo": f"owner/{repo}", "finding": "f", "change": "c", "risk": "low", "ring": ring, "plan_hash": "abc",
            "pr_url": URL.format(repo) if pr else "", "state": state, "ci": "", "last_check": ""}
    base.update(over)
    return base


def view(state="OPEN", draft=False, rollup=None):
    return 0, json.dumps({"state": state, "isDraft": draft, "statusCheckRollup": GOOD if rollup is None else rollup}), ""


class FakeRunner:
    def __init__(self, replies=None, default=None):
        self.replies = dict(replies or {})
        self.default = default or view()
        self.calls = []

    def __call__(self, argv):
        self.calls.append(list(argv))
        reply = self.replies.get(argv[3], self.default)
        return reply.pop(0) if isinstance(reply, list) else reply


class TrackCase(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.dir = Path(temp.name)
        self.path = self.dir / "campaign.tsv"
        self.sleeps = []

    def write(self, rows, header=HEADER):
        lines = ["\t".join(header)] + ["\t".join(r[name] for name in header) for r in rows]
        self.path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def run_main(self, runner, *extra):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = fleet_track.main(
                [str(self.path), *extra], runner=runner, sleep=self.sleeps.append,
                now=lambda: datetime(2026, 11, 6, 12, 0, 0, tzinfo=timezone.utc),
            )
        self.out, self.err = out.getvalue(), err.getvalue()
        return code

    def rows(self, path=None):
        return fleet_track.read_table(path or self.path)[1]


class Refresh(TrackCase):
    def test_refreshes_state_ci_and_last_check_only(self):
        self.write([row("a", ci="stale", finding="keep me", plan_hash="h1")])
        self.assertEqual(self.run_main(FakeRunner(default=view("MERGED"))), 0)
        result = self.rows()[0]
        self.assertEqual((result["state"], result["ci"], result["last_check"]), ("merged", "passing", "2026-11-06T12:00:00Z"))
        self.assertEqual((result["finding"], result["plan_hash"], result["pr_url"]), ("keep me", "h1", URL.format("a")))

    def test_gh_call_shape(self):
        self.write([row("a")])
        runner = FakeRunner()
        self.run_main(runner)
        self.assertEqual(runner.calls, [["gh", "pr", "view", URL.format("a"), "--json", "state,isDraft,statusCheckRollup"]])

    def test_rows_without_a_url_are_untouched(self):
        self.write([row("a", pr=False, state="skipped", last_check="old")])
        runner = FakeRunner()
        self.run_main(runner)
        self.assertEqual(runner.calls, [])
        self.assertEqual(self.rows()[0]["state"], "skipped")
        self.assertEqual(self.rows()[0]["last_check"], "old")

    def test_draft_is_reported(self):
        self.write([row("a")])
        self.run_main(FakeRunner(default=view(draft=True)))
        self.assertEqual(self.rows()[0]["state"], "draft")

    def test_extra_columns_and_order_survive(self):
        header = ["owner", *HEADER, "note"]
        self.write([{**row("a"), "owner": "team-a", "note": 'say "hi"'}], header)
        self.run_main(FakeRunner())
        lines = self.path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[0].split("\t"), header)
        self.assertTrue(lines[1].startswith("team-a\t"))
        self.assertTrue(lines[1].endswith('say "hi"'))

    def test_counts_by_state_print(self):
        self.write([row("a"), row("b")])
        self.run_main(FakeRunner({URL.format("a"): view("MERGED")}))
        self.assertIn("merged: 1", self.out)
        self.assertIn("open: 1", self.out)

    def test_output_goes_elsewhere_and_input_stays(self):
        self.write([row("a")])
        before = self.path.read_text(encoding="utf-8")
        other = self.dir / "out.tsv"
        self.run_main(FakeRunner(default=view("MERGED")), "--output", str(other))
        self.assertEqual(self.path.read_text(encoding="utf-8"), before)
        self.assertEqual(self.rows(other)[0]["state"], "merged")

    def test_shared_pull_request_is_fetched_once(self):
        self.write([row("a"), row("a", finding="second")])
        runner = FakeRunner()
        self.run_main(runner)
        self.assertEqual(len(runner.calls), 1)
        self.assertTrue(all(r["last_check"] for r in self.rows()))

    def test_declined_stays_declined_while_closed(self):
        self.write([row("a", state="declined"), row("b", state="explained"), row("c", state="open")])
        self.run_main(FakeRunner(default=view("CLOSED")))
        self.assertEqual([r["state"] for r in self.rows()], ["declined", "explained", "closed"])

    def test_reopened_overrides_declined(self):
        self.write([row("a", state="declined")])
        self.run_main(FakeRunner())
        self.assertEqual(self.rows()[0]["state"], "open")

    def test_no_temp_files_left(self):
        self.write([row("a")])
        self.run_main(FakeRunner())
        self.assertEqual([p.name for p in self.dir.iterdir()], ["campaign.tsv"])

    def test_child_process_turns_path_conversion_off(self):
        seen = {}

        class Done:
            returncode, stdout, stderr = 0, "", ""

        def fake_run(argv, **kwargs):
            seen.update(kwargs["env"])
            return Done()

        original = fleet_track.subprocess.run
        fleet_track.subprocess.run = fake_run
        self.addCleanup(setattr, fleet_track.subprocess, "run", original)
        fleet_track.run_gh(["gh"])
        self.assertEqual(seen["MSYS_NO_PATHCONV"], "1")


class Ci(unittest.TestCase):
    def test_mapping(self):
        def status(state):
            return {"__typename": "StatusContext", "state": state}

        def run(state, conclusion=""):
            return {"__typename": "CheckRun", "status": state, "conclusion": conclusion}

        cases = [
            (None, "none"), ([], "none"),
            (GOOD, "passing"), (BAD, "failing"),
            ([run("IN_PROGRESS")], "pending"), ([run("QUEUED")], "pending"),
            ([run("COMPLETED", "SKIPPED"), run("COMPLETED", "NEUTRAL")], "passing"),
            ([run("COMPLETED", "TIMED_OUT")], "failing"), ([run("COMPLETED", "CANCELLED")], "failing"),
            ([run("COMPLETED", "ACTION_REQUIRED")], "failing"), ([run("COMPLETED", "STARTUP_FAILURE")], "failing"),
            ([run("COMPLETED", "STALE")], "pending"),
            ([status("SUCCESS")], "passing"), ([status("FAILURE")], "failing"), ([status("ERROR")], "failing"),
            ([status("PENDING")], "pending"), ([status("EXPECTED")], "pending"),
            (GOOD + [run("IN_PROGRESS")], "pending"), (GOOD + [run("IN_PROGRESS")] + BAD, "failing"),
        ]
        for rollup, expected in cases:
            self.assertEqual(fleet_track.ci_from_rollup(rollup), expected, rollup)


class StopRules(TrackCase):
    def ring(self, count):
        return [row(f"r{i}") for i in range(count)]

    def test_ci_exactly_ten_percent_does_not_stop(self):
        self.write(self.ring(10))
        self.assertEqual(self.run_main(FakeRunner({URL.format("r0"): view(rollup=BAD)})), 0)
        self.assertIn("no measured rule fired", self.out)

    def test_ci_above_ten_percent_stops(self):
        self.write(self.ring(10))
        replies = {URL.format("r0"): view(rollup=BAD), URL.format("r1"): view(rollup=BAD)}
        self.assertEqual(self.run_main(FakeRunner(replies)), 1)
        self.assertIn("STOP: CI failed on 2 of 10", self.out)

    def test_rings_are_judged_apart(self):
        self.write([row("a", ring="pilot"), row("b", ring="50"), row("c", ring="50")])
        self.assertEqual(self.run_main(FakeRunner({URL.format("a"): view(rollup=BAD)})), 1)
        lines = self.out.splitlines()
        pilot = next(i for i, line in enumerate(lines) if line.strip().startswith("pilot:"))
        fifty = next(i for i, line in enumerate(lines) if line.strip().startswith("50:"))
        self.assertIn("STOP", lines[pilot + 1])
        self.assertIn("no measured rule fired", lines[fifty + 1])

    def test_one_closed_does_not_stop_two_do(self):
        self.write(self.ring(5))
        self.assertEqual(self.run_main(FakeRunner({URL.format("r0"): view("CLOSED")})), 0)
        self.assertEqual(
            self.run_main(FakeRunner({URL.format("r0"): view("CLOSED"), URL.format("r1"): view("CLOSED")})), 1
        )
        self.assertIn("2 pull requests closed unmerged", self.out)

    def test_declined_counts_and_explained_clears(self):
        self.write([row("a", state="declined"), row("b", state="declined")])
        self.assertEqual(self.run_main(FakeRunner(default=view("CLOSED"))), 1)
        self.write([row("a", state="declined"), row("b", state="explained")])
        self.assertEqual(self.run_main(FakeRunner(default=view("CLOSED"))), 0)

    def test_damage_flag_stops(self):
        self.write([row("a")])
        self.assertEqual(self.run_main(FakeRunner(), "--damage", "10"), 1)
        self.assertIn("damage reported", self.out)

    def test_manual_rules_are_never_reported_as_passed(self):
        self.write([row("a")])
        self.run_main(FakeRunner())
        self.assertIn("damage not reported to this script", self.out)
        self.assertIn("Manual checks", self.out)

    def test_secondary_hits_flag_stops_at_two(self):
        self.write([row("a")])
        self.assertEqual(self.run_main(FakeRunner(), "--secondary-hits", "10=1"), 0)
        self.assertEqual(self.run_main(FakeRunner(), "--secondary-hits", "10=2"), 1)
        self.assertIn("2 secondary rate limits", self.out)

    def test_shared_pull_request_counts_once(self):
        rows = [row("a"), row("a", finding="second")] + [row(f"r{i}") for i in range(9)]
        self.write(rows)
        self.assertEqual(self.run_main(FakeRunner({URL.format("a"): view(rollup=BAD)})), 0)


class Failures(TrackCase):
    def test_option_like_url_never_reaches_gh(self):
        self.write([row("a", pr_url="--web"), row("b", pr_url="https://example.com/x/y/pull/1"), row("c", pr_url="https://github.com/o/r/pull/1 --web")])
        runner = FakeRunner()
        self.assertEqual(self.run_main(runner), 1)
        self.assertEqual(runner.calls, [])
        self.assertIn("not a GitHub pull request URL", self.out)
        self.assertEqual(self.rows()[0]["pr_url"], "--web")

    def test_unresolved_pull_request_becomes_unknown(self):
        err = "GraphQL: Could not resolve to a PullRequest with the number of 9. (repository.pullRequest)"
        self.write([row("a", state="open")])
        self.assertEqual(self.run_main(FakeRunner(default=(1, "", err))), 1)
        self.assertEqual(self.rows()[0]["state"], "unknown")

    def test_transient_failure_keeps_the_row(self):
        self.write([row("a", state="merged", ci="passing", last_check="old")])
        self.assertEqual(self.run_main(FakeRunner(default=(1, "", "connection reset"))), 1)
        result = self.rows()[0]
        self.assertEqual((result["state"], result["ci"], result["last_check"]), ("merged", "passing", "old"))

    def test_secondary_limit_backs_off_and_counts(self):
        err = (1, "", "You have exceeded a secondary rate limit")
        self.write([row("a")])
        self.assertEqual(self.run_main(FakeRunner({URL.format("a"): [err, view()]})), 0)
        self.assertEqual(self.sleeps, [60])
        self.write([row("a")])
        self.assertEqual(self.run_main(FakeRunner({URL.format("a"): [err, err, view()]})), 1)
        self.assertIn("2 secondary rate limits", self.out)

    def test_rate_limit_exhausted_stops_and_saves_earlier_rows(self):
        self.write([row("a"), row("b"), row("c")])
        runner = FakeRunner({URL.format("a"): view("MERGED"), URL.format("b"): (1, "", "API rate limit exceeded")})
        self.assertEqual(self.run_main(runner), 1)
        self.assertEqual(self.sleeps, [60, 120, 240])
        rows = self.rows()
        self.assertEqual(rows[0]["state"], "merged")
        self.assertEqual(rows[2]["last_check"], "")
        self.assertFalse(any(URL.format("c") in call for call in runner.calls))

    def test_missing_column_is_exit_2(self):
        self.write([row("a")], [c for c in HEADER if c != "ci"])
        before = self.path.read_text(encoding="utf-8")
        self.assertEqual(self.run_main(FakeRunner()), 2)
        self.assertEqual(self.path.read_text(encoding="utf-8"), before)

    def test_short_row_is_exit_2(self):
        self.path.write_text("\t".join(HEADER) + "\nonly\ttwo\n", encoding="utf-8")
        self.assertEqual(self.run_main(FakeRunner()), 2)
        self.assertIn("line 2", self.err)

    def test_missing_file_is_exit_2(self):
        self.assertEqual(self.run_main(FakeRunner()), 2)

    def test_bom_and_crlf_are_read(self):
        text = "﻿" + "\t".join(HEADER) + "\r\n" + "\t".join(row("a")[c] for c in HEADER) + "\r\n"
        self.path.write_bytes(text.encode("utf-8"))
        self.assertEqual(self.run_main(FakeRunner()), 0)
        self.assertEqual(self.rows()[0]["repo"], "owner/a")

    def test_unknown_ring_flag_is_exit_2(self):
        self.write([row("a")])
        runner = FakeRunner()
        self.assertEqual(self.run_main(runner, "--damage", "nope"), 2)
        self.assertEqual(runner.calls, [])

    def test_auth_failure_is_exit_2_and_leaves_the_file(self):
        self.write([row("a")])
        before = self.path.read_text(encoding="utf-8")
        self.assertEqual(self.run_main(FakeRunner(default=(1, "", "please run: gh auth login"))), 2)
        self.assertEqual(self.path.read_text(encoding="utf-8"), before)

    def test_tokens_never_print(self):
        secret = "ghp_" + "b" * 36
        self.write([row("a")])
        self.run_main(FakeRunner(default=(1, "", f"boom {secret}")))
        self.assertNotIn(secret, self.out + self.err)


if __name__ == "__main__":
    unittest.main()
