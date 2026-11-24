"""Tests for home/.local/bin/workstreams.

Run with `mise run test`. Each test builds a throwaway repo with trackers and
handoffs and runs the script in it.
"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "home/.local/bin/workstreams"


def tracker(status: str) -> str:
    return f"# name\n\n**Status:** {status}\n\n## Goal\n"


def handoff(workstream: str) -> str:
    return f"---\ndate: x\nworkstream: {workstream}\nprevious: none\n---\n"


class WorkstreamsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        (self.repo / ".claude/tracking").mkdir(parents=True)
        (self.repo / ".claude/handoffs").mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, rel: str, text: str) -> Path:
        path = self.repo / ".claude" / rel
        path.write_text(text)
        return path

    def run_script(self, *args: str, cwd: Path | None = None) -> str:
        env = {k: v for k, v in os.environ.items() if k != "NO_COLOR"}
        return subprocess.run(
            [str(SCRIPT), *args],
            cwd=cwd or self.repo,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        ).stdout

    def test_sorts_by_newest_handoff_and_hides_done(self):
        self.write("tracking/old.md", tracker("active. old"))
        self.write("tracking/new.md", tracker("active. new"))
        self.write("tracking/closed.md", tracker("done. shipped"))
        self.write("handoffs/2026-01-01-0900-a.md", handoff("old"))
        self.write("handoffs/2026-02-01-0900-b.md", handoff("new"))
        self.write("handoffs/2026-03-01-0900-c.md", handoff("closed"))

        self.assertEqual(self.run_script("--names").split(), ["new", "old"])
        out = self.run_script()
        self.assertIn("new  2026-02-01 09:00  active. new", out)
        self.assertIn("(1 done hidden; --all shows them)", out)
        self.assertEqual(
            self.run_script("--all", "--names").split(), ["closed", "new", "old"]
        )

    def test_newest_handoff_wins_regardless_of_file_order(self):
        self.write("tracking/ws.md", tracker("active. x"))
        self.write("handoffs/2026-05-01-1200-later.md", handoff("ws"))
        self.write("handoffs/2026-04-01-1200-earlier.md", handoff("ws"))
        self.assertIn("2026-05-01 12:00", self.run_script())

    def test_lists_chains_without_a_tracker(self):
        self.write("handoffs/2026-01-01-0900-a.md", handoff("legacy"))
        self.assertIn("legacy  2026-01-01 09:00  (no tracker", self.run_script())

    def test_tracker_without_handoff_uses_its_mtime(self):
        path = self.write("tracking/fresh.md", tracker("active. x"))
        stamp = 1767261600  # 2026-01-01 10:00 UTC
        os.utime(path, (stamp, stamp))
        self.assertIn("fresh", self.run_script("--names"))

    def test_finds_main_worktree_from_a_subdirectory(self):
        self.write("tracking/ws.md", tracker("active. x"))
        sub = self.repo / "deep/dir"
        sub.mkdir(parents=True)
        self.assertEqual(self.run_script("--names", cwd=sub).split(), ["ws"])

    def test_reports_no_active_workstreams(self):
        self.write("tracking/closed.md", tracker("done. shipped"))
        self.assertIn("No active workstreams", self.run_script())
        self.assertIn("1 done", self.run_script())

    def test_color_only_when_asked_or_on_a_terminal(self):
        self.write("tracking/ws.md", tracker("active. x"))
        self.assertNotIn("\033[", self.run_script())  # stdout is a pipe
        self.assertIn("\033[32mactive.\033[0m", self.run_script("--color=always"))


if __name__ == "__main__":
    unittest.main()
