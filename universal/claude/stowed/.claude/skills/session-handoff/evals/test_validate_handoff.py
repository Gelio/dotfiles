#!/usr/bin/env python3
"""Regression tests for validate_handoff section detection.

Covers softaworks/agent-toolkit#21: required/recommended sections must be
detected at any Markdown heading depth, not just level 1-2. The skill's own
template emits required sections at level 3 (e.g. `### Important Context`),
which the old `##?` regex falsely reported as missing.

Run directly:
    python3 evals/test_validate_handoff.py
"""

import importlib.util
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = SKILL_ROOT / "scripts" / "validate_handoff.py"
TEMPLATE_PATH = SKILL_ROOT / "references" / "handoff-template.md"

spec = importlib.util.spec_from_file_location("validate_handoff", MODULE_PATH)
validate_handoff = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(validate_handoff)


# Required sections at level 3 + recommended sections, each with enough content
# to clear the 50-char completeness threshold so we isolate heading detection.
THIRD_LEVEL_HANDOFF = """# Handoff: Example

### Current State Summary
This section explains the current state in enough detail for the next agent to
pick up the work without rediscovering the plan from scratch.

### Important Context
The validator must accept deeper heading levels because real handoffs nest
required sections under a top-level document title before the content.

### Immediate Next Steps
Patch the regex, run the regression test, and confirm the report flips from
FAIL to PASS for the required sections.

### Architecture Overview
The script validates sections, scans for secrets, and checks file references.

### Critical Files
The main file is scripts/validate_handoff.py in the skill directory tree.

### Files Modified
This change touches the validator regex and adds this regression test module.

### Decisions Made
Allow any standard Markdown heading level instead of hard-coding level two.

### Assumptions Made
Handoff files may use nested section headings under a single document title.

### Potential Gotchas
A deeper subheading now bounds a parent section's content-length measurement.
"""


# Legacy level-2 format must keep validating (no regression).
SECOND_LEVEL_HANDOFF = """# Handoff: Example

## Current State Summary
This confirms the previous level-two format still passes after the validator is
updated to accept deeper headings as well.

## Important Context
Backward compatibility matters because existing handoffs use second-level
headings and should keep validating cleanly.

## Immediate Next Steps
Run the checks against both legacy and nested heading examples to verify the
broader heading regex does not regress older files.
"""


class SectionHeadingDetectionTests(unittest.TestCase):
    def test_accepts_level_three_required_and_recommended_sections(self):
        required_complete, missing_required = validate_handoff.check_required_sections(
            THIRD_LEVEL_HANDOFF
        )
        missing_recommended = validate_handoff.check_recommended_sections(
            THIRD_LEVEL_HANDOFF
        )

        self.assertTrue(required_complete, missing_required)
        self.assertEqual(missing_required, [])
        self.assertEqual(missing_recommended, [])

    def test_keeps_support_for_level_two_required_sections(self):
        required_complete, missing_required = validate_handoff.check_required_sections(
            SECOND_LEVEL_HANDOFF
        )

        self.assertTrue(required_complete, missing_required)
        self.assertEqual(missing_required, [])

    def test_bundled_template_required_sections_are_detected(self):
        """The skill's own template uses mixed heading levels; required sections
        must be detected regardless of depth. Placeholders are filled so the
        completeness check tests heading detection, not content length."""
        template = TEMPLATE_PATH.read_text()
        # Replace [PLACEHOLDER] / [TODO ...] spans with real content so the
        # 50-char completeness check passes for detected sections.
        filled = re.sub(
            r"\[[^\]]*\]",
            "placeholder content that is comfortably longer than fifty chars",
            template,
        )

        for section in validate_handoff.REQUIRED_SECTIONS:
            pattern = rf"{validate_handoff.SECTION_HEADING_PATTERN}{re.escape(section)}"
            self.assertRegex(
                filled,
                pattern,
                f"required section not detected in template: {section}",
            )


class FileReferenceResolutionTests(unittest.TestCase):
    """References resolve against the repo root from `Project:` metadata, and
    tolerate paths written relative to a working subdirectory.

    Handoffs are stored centrally (~/.local/claude-handoffs/<repo-key>/...), so
    the old `parent.parent.parent` base no longer points at the repo; the
    validator now reads `Project:` and also matches files by path-suffix.
    """

    def setUp(self):
        self.repo = tempfile.mkdtemp(prefix="handoff-test-repo.")
        subprocess.run(["git", "-C", self.repo, "init", "-q"], check=True)
        sub = Path(self.repo) / "universal" / "claude" / "scripts"
        sub.mkdir(parents=True)
        (sub / "thing.py").write_text("x = 1\n")  # untracked, but real

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)

    def _handoff(self, body: str) -> str:
        return f"# Handoff: T\n\n## Session Metadata\n- Project: {self.repo}\n\n{body}\n"

    def test_extract_project_root_uses_project_metadata(self):
        content = self._handoff("body")
        handoff_path = Path(self.repo) / ".claude" / "handoffs" / "key" / "h.md"
        root = validate_handoff.extract_project_root(content, handoff_path)
        self.assertEqual(Path(root), Path(self.repo))

    def test_subdir_relative_reference_resolves_via_suffix(self):
        # Path written relative to universal/claude (a subdir), not the repo root.
        content = self._handoff("| scripts/thing.py | changed | because |")
        existing, missing, _external = validate_handoff.check_file_references(content, self.repo)
        self.assertIn("scripts/thing.py", existing)
        self.assertEqual(missing, [])

    def test_root_relative_reference_resolves(self):
        content = self._handoff("`universal/claude/scripts/thing.py`")
        existing, missing, _external = validate_handoff.check_file_references(content, self.repo)
        self.assertIn("universal/claude/scripts/thing.py", existing)
        self.assertEqual(missing, [])

    def test_genuinely_missing_reference_is_reported(self):
        content = self._handoff("| scripts/nope.py | x | y |")
        existing, missing, _external = validate_handoff.check_file_references(content, self.repo)
        self.assertIn("scripts/nope.py", missing)

    def test_existing_absolute_path_resolves(self):
        # Absolute paths (e.g. a backup tarball outside the repo) must be checked
        # on disk directly, not resolved relative to the repo root.
        abs_file = Path(self.repo) / "backup.tar.gz"
        abs_file.write_text("data\n")
        content = self._handoff(f"Backup: `{abs_file}`")
        existing, missing, _external = validate_handoff.check_file_references(content, self.repo)
        self.assertIn(str(abs_file), existing)
        self.assertEqual(missing, [])

    def test_genuinely_missing_absolute_path_within_repo_is_reported(self):
        # An absolute path that lives *inside* a known repo but is gone is a
        # genuine deletion -> WARN bucket, not the non-alarming external bucket.
        abs_file = Path(self.repo) / "does-not-exist.tar.gz"
        content = self._handoff(f"Backup: `{abs_file}`")
        existing, missing, external = validate_handoff.check_file_references(content, self.repo)
        self.assertIn(str(abs_file), missing)
        self.assertNotIn(str(abs_file), external)

    def test_out_of_repo_absolute_scratch_path_is_external_not_missing(self):
        # A scratch path outside every known repo (e.g. /private/tmp) must not
        # masquerade as a deleted in-repo file.
        scratch = "/private/tmp/claude/pr-body-does-not-exist.md"
        content = self._handoff(f"Body from `{scratch}`")
        existing, missing, external = validate_handoff.check_file_references(content, self.repo)
        self.assertIn(scratch, external)
        self.assertNotIn(scratch, missing)


class ProjectRootExtractionTests(unittest.TestCase):
    """`extract_project_root` must tolerate label/formatting variants and refuse
    to silently fall back to cwd when no usable root can be determined."""

    def setUp(self):
        self.repo = tempfile.mkdtemp(prefix="handoff-test-root.")
        subprocess.run(["git", "-C", self.repo, "init", "-q"], check=True)
        # A non-git tree for handoffs whose root cannot be determined, so the
        # legacy `parent.parent.parent/.git` fallback does not accidentally fire.
        self.nongit = tempfile.mkdtemp(prefix="handoff-test-nongit.")

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)
        shutil.rmtree(self.nongit, ignore_errors=True)

    def _handoff(self, project_line: str) -> str:
        return f"# Handoff: T\n\n## Session Metadata\n{project_line}\n\nbody\n"

    def test_parenthetical_and_backtick_label_variant(self):
        # The repro: `- Project (handoff chain home): ` + backtick-wrapped path
        # + trailing prose. The plain `Project:` regex missed all of this.
        content = self._handoff(
            f"- Project (handoff chain home): `{self.repo}` (chain lives here; ignore this)"
        )
        handoff_path = Path(self.repo) / "h.md"
        root = validate_handoff.extract_project_root(content, handoff_path)
        self.assertEqual(Path(root), Path(self.repo))

    def test_returns_none_when_root_undeterminable(self):
        # Project points at a nonexistent path and the handoff does not sit in a
        # legacy in-repo layout -> distinct "undetermined", never cwd.
        content = self._handoff("- Project: /no/such/path/anywhere-12345")
        handoff_path = Path(self.nongit) / "a" / "b" / "c" / "h.md"
        root = validate_handoff.extract_project_root(content, handoff_path)
        self.assertIsNone(root)

    def test_undetermined_root_skips_reference_check(self):
        content = self._handoff("- Project: /no/such/path/anywhere-12345")
        deep = Path(self.nongit) / "a" / "b" / "c"
        deep.mkdir(parents=True)
        path = deep / "h.md"
        path.write_text(content + "\n`some/deleted/file.py`\n")
        result = validate_handoff.validate_handoff(str(path))
        self.assertTrue(result.get("root_undetermined"))
        self.assertEqual(result["files_missing"], [])


class CrossRepoReferenceTests(unittest.TestCase):
    """Cross-repo handoffs: the chain lives in one repo while the work (and its
    file references) live in a sibling repo. References rooted in a known sibling
    repo must resolve as *found*, not as missing."""

    def setUp(self):
        self.parent = tempfile.mkdtemp(prefix="handoff-test-multi.")
        self.primary = Path(self.parent) / "nexus-tests"
        self.sibling = Path(self.parent) / "edbpgai-bootstrap"
        for repo in (self.primary, self.sibling):
            repo.mkdir()
            subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
        # Two real files in the sibling repo, referenced two different ways.
        wf = self.sibling / ".github" / "workflows"
        wf.mkdir(parents=True)
        (wf / "prevent_update.yml").write_text("on: push\n")
        tmpl = self.sibling / "deploy" / "charts" / "edbpgai-bootstrap"
        tmpl.mkdir(parents=True)
        (tmpl / "values.yaml.template").write_text("x: 1\n")

    def tearDown(self):
        shutil.rmtree(self.parent, ignore_errors=True)

    def _handoff(self, body: str) -> str:
        return (
            f"# Handoff: T\n\n## Session Metadata\n"
            f"- Project (handoff chain home): `{self.primary}`\n\n{body}\n"
        )

    def test_sibling_prefixed_reference_resolves(self):
        # First path segment names the sibling repo dir -> rooted at the parent.
        content = self._handoff("`edbpgai-bootstrap/.github/workflows/prevent_update.yml`")
        existing, missing, _external = validate_handoff.check_file_references(
            content, str(self.primary)
        )
        self.assertIn("edbpgai-bootstrap/.github/workflows/prevent_update.yml", existing)
        self.assertEqual(missing, [])

    def test_sibling_repo_root_relative_reference_resolves(self):
        # Reference written relative to the sibling repo *root* (no repo-name
        # prefix). The sibling repo is discovered via the other reference's
        # first segment, then this one resolves through its file index.
        content = self._handoff(
            "`edbpgai-bootstrap/.github/workflows/prevent_update.yml` and "
            "`deploy/charts/edbpgai-bootstrap/values.yaml.template`"
        )
        existing, missing, _external = validate_handoff.check_file_references(
            content, str(self.primary)
        )
        self.assertIn("deploy/charts/edbpgai-bootstrap/values.yaml.template", existing)
        self.assertEqual(missing, [])

    def test_additional_working_dir_from_absolute_prose_path(self):
        # The sibling repo is named only as an absolute path in prose (no
        # sibling-prefixed reference). It must still be discovered as a
        # candidate root so its repo-root-relative references resolve.
        content = self._handoff(
            f"Work happened in `{self.sibling}`.\n\n"
            "`deploy/charts/edbpgai-bootstrap/values.yaml.template`"
        )
        existing, missing, _external = validate_handoff.check_file_references(
            content, str(self.primary)
        )
        self.assertIn("deploy/charts/edbpgai-bootstrap/values.yaml.template", existing)
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
