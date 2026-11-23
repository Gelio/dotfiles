"""Tests for merge_local.py and the scripts that share its view of an overlay.

Run with `mise run test`.
"""

import importlib.util
import tempfile
import tomllib
import unittest
from pathlib import Path

import merge_local

HERE = Path(__file__).resolve().parent


def load_script(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guard = load_script("merge_guard", HERE / "merge-guard.py")
review = load_script("review_settings", HERE.parent / "agents/review-settings.py")


def hook(command: str) -> dict:
    return {"type": "command", "command": command}


class CombineTest(unittest.TestCase):
    def test_arrays_append_and_scalars_replace(self):
        shared = {"a": ["x", "y"], "b": True, "c": {"d": 1}}
        local = {"a": ["y", "z"], "b": False, "c": {"e": 2}}
        self.assertEqual(
            merge_local.combine(shared, local),
            {"a": ["x", "y", "z"], "b": False, "c": {"d": 1, "e": 2}},
        )

    def test_hook_group_joins_the_group_with_its_matcher(self):
        shared = [{"matcher": "", "hooks": [hook("a")]}]
        local = [
            {"matcher": "", "hooks": [hook("b")]},
            {"matcher": "Bash", "hooks": [hook("c")]},
        ]
        self.assertEqual(
            merge_local.combine(shared, local),
            [
                {"matcher": "", "hooks": [hook("a"), hook("b")]},
                {"matcher": "Bash", "hooks": [hook("c")]},
            ],
        )

    def test_group_without_matcher_matches_empty_matcher(self):
        shared = [{"hooks": [hook("a")]}]
        local = [{"matcher": "", "hooks": [hook("b")]}]
        combined = merge_local.combine(shared, local)
        self.assertEqual(len(combined), 1)
        self.assertEqual(combined[0]["hooks"], [hook("a"), hook("b")])


class HookInSharedGroupTest(unittest.TestCase):
    """A live hook added to a matcher group the partial already has."""

    def setUp(self):
        self.partial = {
            "hooks": {"PreToolUse": [{"matcher": "", "hooks": [hook("a")]}]}
        }

    def localize_all(self, live: dict) -> dict:
        """Answer [l]ocal to everything review-settings.py offers."""
        overlay = {}
        for _key, _heading, _body, apply in review.find_candidates(self.partial, live):
            apply(overlay)
        return overlay

    def check(self, live_hooks: list):
        live = {"hooks": {"PreToolUse": [{"matcher": "", "hooks": live_hooks}]}}
        self.assertEqual(len(list(guard.losses(self.partial, live, ""))), 1)

        overlay = self.localize_all(live)
        known = merge_local.combine(self.partial, overlay)
        self.assertEqual(list(review.find_candidates(known, live)), [])
        self.assertEqual(list(guard.losses(known, live, "")), [])

    def test_hook_after_the_shared_one(self):
        self.check([hook("a"), hook("h")])

    def test_hook_before_the_shared_one(self):
        self.check([hook("h"), hook("a")])


class TomlTest(unittest.TestCase):
    def test_round_trip(self):
        data = {
            "a": 1,
            "s": 'tab\t quote" del\x7f nul\x00 é',
            "tui": {"status_line": ["x", "y"], "colors": True},
            "x.y": {"k": "v"},
            "arr": [{"name": "t"}],
            "p": {"q r": {"s": {"t": 1.5}}},
        }
        self.assertEqual(tomllib.loads(merge_local.toml_dumps(data)), data)

    def test_del_is_escaped(self):
        self.assertNotIn("\x7f", merge_local.toml_dumps({"k\x7f": "v\x7f"}))


class InvalidFileTest(unittest.TestCase):
    def check(self, name: str, text: str):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / name
            path.write_text(text)
            with self.assertRaises(merge_local.InvalidFile) as raised:
                merge_local.load(path)
            self.assertIn(str(path), str(raised.exception))

    def test_empty_json(self):
        self.check("settings.json", "")

    def test_invalid_json(self):
        self.check("settings.json", "{")

    def test_empty_toml(self):
        self.check("config.toml", "\n")

    def test_invalid_toml(self):
        self.check("config.toml", "a = ")


if __name__ == "__main__":
    unittest.main()
