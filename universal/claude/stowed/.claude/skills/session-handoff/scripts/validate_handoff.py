#!/usr/bin/env python3
"""
Validate a handoff document for completeness and quality.

Checks:
- No TODO placeholders remaining
- Required sections present and populated
- No potential secrets detected
- Referenced files exist
- Quality scoring

Usage:
    python validate_handoff.py <handoff-file>
    python validate_handoff.py .claude/handoffs/2024-01-15-143022-auth.md
"""

import os
import re
import subprocess
import sys
from pathlib import Path

# Secret detection patterns
SECRET_PATTERNS = [
    (r'["\']?[a-zA-Z_]*api[_-]?key["\']?\s*[:=]\s*["\'][^"\']{10,}["\']', "API key"),
    (r'["\']?[a-zA-Z_]*password["\']?\s*[:=]\s*["\'][^"\']+["\']', "Password"),
    (r'["\']?[a-zA-Z_]*secret["\']?\s*[:=]\s*["\'][^"\']{10,}["\']', "Secret"),
    (r'["\']?[a-zA-Z_]*token["\']?\s*[:=]\s*["\'][^"\']{20,}["\']', "Token"),
    (r'["\']?[a-zA-Z_]*private[_-]?key["\']?\s*[:=]', "Private key"),
    (r'-----BEGIN [A-Z]+ PRIVATE KEY-----', "PEM private key"),
    (r'mongodb(\+srv)?://[^/\s]+:[^@\s]+@', "MongoDB connection string with password"),
    (r'postgres://[^/\s]+:[^@\s]+@', "PostgreSQL connection string with password"),
    (r'mysql://[^/\s]+:[^@\s]+@', "MySQL connection string with password"),
    (r'Bearer\s+[a-zA-Z0-9_\-\.]+', "Bearer token"),
    (r'ghp_[a-zA-Z0-9]{36}', "GitHub personal access token"),
    (r'sk-[a-zA-Z0-9]{48}', "OpenAI API key"),
    (r'xox[baprs]-[a-zA-Z0-9-]+', "Slack token"),
]

# Required sections for a complete handoff
REQUIRED_SECTIONS = [
    "Current State Summary",
    "Important Context",
    "Immediate Next Steps",
]

# Recommended sections
RECOMMENDED_SECTIONS = [
    "Architecture Overview",
    "Critical Files",
    "Files Modified",
    "Decisions Made",
    "Assumptions Made",
    "Potential Gotchas",
]

# Accept any standard Markdown heading level (# through ######) for sections.
SECTION_HEADING_PATTERN = r'(?:^|\n)#{1,6}\s*'
NEXT_HEADING_PATTERN = r'\n#{1,6}\s+'


def check_todos(content: str) -> tuple[bool, list[str]]:
    """Check for remaining TODO placeholders."""
    todos = re.findall(r'\[TODO:[^\]]*\]', content)
    return len(todos) == 0, todos


def check_required_sections(content: str) -> tuple[bool, list[str]]:
    """Check that required sections exist and have content."""
    missing = []
    for section in REQUIRED_SECTIONS:
        # Look for section header at any heading depth
        pattern = rf'{SECTION_HEADING_PATTERN}{re.escape(section)}'
        match = re.search(pattern, content, re.IGNORECASE)
        if not match:
            missing.append(f"{section} (missing)")
        else:
            # Check if section has meaningful content (not just placeholder)
            section_start = match.end()
            next_section = re.search(NEXT_HEADING_PATTERN, content[section_start:])
            section_end = section_start + next_section.start() if next_section else len(content)
            section_content = content[section_start:section_end].strip()

            # 50 chars minimum: roughly 1-2 sentences, enough to convey meaningful context
            if len(section_content) < 50 or '[TODO' in section_content:
                missing.append(f"{section} (incomplete)")

    return len(missing) == 0, missing


def check_recommended_sections(content: str) -> list[str]:
    """Check which recommended sections are missing."""
    missing = []
    for section in RECOMMENDED_SECTIONS:
        pattern = rf'{SECTION_HEADING_PATTERN}{re.escape(section)}'
        if not re.search(pattern, content, re.IGNORECASE):
            missing.append(section)
    return missing


def scan_for_secrets(content: str) -> list[tuple[str, str]]:
    """Scan content for potential secrets."""
    findings = []
    for pattern, description in SECRET_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            findings.append((description, f"Found {len(matches)} potential match(es)"))
    return findings


def extract_project_root(content: str, handoff_path: Path) -> str:
    """Determine the repo root that referenced paths are relative to.

    Uses the handoff's `Project:` metadata (the origin repo root). Handoffs are
    stored centrally (`~/.local/claude-handoffs/<repo-key>/...`), so the old
    parent.parent.parent heuristic no longer points at the repo.
    """
    match = re.search(r'^\s*[-*]?\s*Project:\s*(.+?)\s*$', content, re.MULTILINE)
    if match:
        candidate = match.group(1).strip().strip('`').strip()
        expanded = Path(candidate).expanduser()
        if candidate and expanded.exists():
            return str(expanded)
    # Fallbacks: legacy in-repo layout, then the current directory.
    legacy = handoff_path.parent.parent.parent
    if (legacy / ".git").exists():
        return str(legacy)
    return os.getcwd()


def repo_file_index(project_root: str) -> set[str]:
    """All real files in the repo (tracked + untracked-but-not-ignored), as
    repo-root-relative POSIX paths. Lets references written relative to a
    working subdirectory still resolve, instead of false-positive warnings."""
    try:
        result = subprocess.run(
            ["git", "-C", project_root, "ls-files",
             "--cached", "--others", "--exclude-standard"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return {line for line in result.stdout.split("\n") if line}
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return set()


def check_file_references(content: str, project_root: str) -> tuple[list[str], list[str]]:
    """Check whether referenced files exist.

    A reference counts as found if it resolves under the repo root OR matches a
    file anywhere in the repo by path suffix (so paths written relative to a
    working subdirectory still resolve). Genuinely absent / deleted files are
    still reported.
    """
    # Pattern 1: | path/to/file | in tables
    # Pattern 2: `path/to/file` in code
    # Pattern 3: path/to/file:123 with line numbers
    patterns = [
        r'\|\s*([a-zA-Z0-9_\-./]+\.[a-zA-Z]+)\s*\|',  # Table cells
        r'`([a-zA-Z0-9_\-./]+\.[a-zA-Z]+(?::\d+)?)`',  # Inline code
        r'(?:^|\s)([a-zA-Z0-9_\-./]+\.[a-zA-Z]+:\d+)',  # With line numbers
    ]

    found_files = set()
    for pattern in patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            # Remove line numbers
            filepath = match.split(':')[0]
            # Skip obvious non-files
            if filepath and not filepath.startswith('http') and '/' in filepath:
                found_files.add(filepath)

    repo_files = repo_file_index(project_root)
    existing = []
    missing = []

    for filepath in found_files:
        rel = filepath.lstrip('./')
        resolves = (Path(project_root) / rel).exists() or any(
            f == rel or f.endswith('/' + rel) for f in repo_files
        )
        (existing if resolves else missing).append(filepath)

    return existing, missing


def calculate_quality_score(
    todos_clear: bool,
    required_complete: bool,
    missing_required: list,
    missing_recommended: list,
    secrets_found: list,
    files_missing: list
) -> tuple[int, str]:
    """Calculate overall quality score (0-100).

    Scoring rationale:
    - Start at 100, deduct for issues
    - TODOs remaining (-30): Indicates incomplete work, major blocker
    - Missing required sections (-10 each): Core context gaps
    - Secrets detected (-20): Security risk, must be fixed
    - Missing file refs (-5 each, max -20): Stale references
    - Missing recommended (-2 each): Nice-to-have completeness
    """
    score = 100

    # Deductions with justifications
    if not todos_clear:
        # -30: TODOs indicate unfinished work; next agent will lack critical info
        score -= 30
    if not required_complete:
        # -10 per section: Required sections are essential for handoff continuity
        score -= 10 * len(missing_required)
    if secrets_found:
        # -20: Security risk; handoffs may be shared or stored in repos
        score -= 20
    if files_missing:
        # -5 per file (max 4): Indicates stale refs; cap at -20 to avoid over-penalizing
        score -= 5 * min(len(files_missing), 4)

    # -2 per section: Recommended but not critical; minor impact on handoff quality
    score -= 2 * len(missing_recommended)

    score = max(0, score)

    # Rating thresholds based on handoff usability:
    # 90+: Comprehensive, ready to use immediately
    # 70-89: Usable with minor gaps
    # 50-69: Needs work before reliable handoff
    # <50: Too incomplete to be useful
    if score >= 90:
        rating = "Excellent - Ready for handoff"
    elif score >= 70:
        rating = "Good - Minor improvements suggested"
    elif score >= 50:
        rating = "Fair - Needs attention before handoff"
    else:
        rating = "Poor - Significant work needed"

    return score, rating


def validate_handoff(filepath: str) -> dict:
    """Run all validations on a handoff file."""
    path = Path(filepath)

    if not path.exists():
        return {"error": f"File not found: {filepath}"}

    content = path.read_text()
    project_root = extract_project_root(content, path)

    # Run checks
    todos_clear, remaining_todos = check_todos(content)
    required_complete, missing_required = check_required_sections(content)
    missing_recommended = check_recommended_sections(content)
    secrets_found = scan_for_secrets(content)
    existing_files, missing_files = check_file_references(content, project_root)

    # Calculate score
    score, rating = calculate_quality_score(
        todos_clear, required_complete, missing_required,
        missing_recommended, secrets_found, missing_files
    )

    return {
        "filepath": str(path),
        "project_root": project_root,
        "score": score,
        "rating": rating,
        "todos_clear": todos_clear,
        "remaining_todos": remaining_todos[:5],  # Limit output
        "todo_count": len(remaining_todos) if not todos_clear else 0,
        "required_complete": required_complete,
        "missing_required": missing_required,
        "missing_recommended": missing_recommended,
        "secrets_found": secrets_found,
        "files_verified": len(existing_files),
        "files_missing": missing_files[:5],  # Limit output
    }


def print_report(result: dict):
    """Print a formatted validation report."""
    if "error" in result:
        print(f"Error: {result['error']}")
        return False

    print(f"\n{'='*60}")
    print(f"Handoff Validation Report")
    print(f"{'='*60}")
    print(f"File: {result['filepath']}")
    print(f"\nQuality Score: {result['score']}/100 - {result['rating']}")
    print(f"{'='*60}")

    # TODOs
    if result['todos_clear']:
        print("\n[PASS] No TODO placeholders remaining")
    else:
        print(f"\n[FAIL] {result['todo_count']} TODO placeholders found:")
        for todo in result['remaining_todos']:
            print(f"       - {todo[:50]}...")

    # Required sections
    if result['required_complete']:
        print("\n[PASS] All required sections complete")
    else:
        print("\n[FAIL] Missing/incomplete required sections:")
        for section in result['missing_required']:
            print(f"       - {section}")

    # Secrets
    if not result['secrets_found']:
        print("\n[PASS] No potential secrets detected")
    else:
        print("\n[WARN] Potential secrets detected:")
        for secret_type, detail in result['secrets_found']:
            print(f"       - {secret_type}: {detail}")

    # File references
    if result['files_missing']:
        print(f"\n[WARN] {len(result['files_missing'])} referenced file(s) not found:")
        print(f"       (resolved relative to repo root: {result['project_root']})")
        for f in result['files_missing']:
            print(f"       - {f}")
    else:
        print(f"\n[INFO] {result['files_verified']} file reference(s) verified")

    # Recommended sections
    if result['missing_recommended']:
        print(f"\n[INFO] Consider adding these sections:")
        for section in result['missing_recommended']:
            print(f"       - {section}")

    print(f"\n{'='*60}")

    # Final verdict
    if result['score'] >= 70 and not result['secrets_found']:
        print("Verdict: READY for handoff")
        return True
    elif result['secrets_found']:
        print("Verdict: BLOCKED - Remove secrets before handoff")
        return False
    else:
        print("Verdict: NEEDS WORK - Complete required sections")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_handoff.py <handoff-file>")
        print("Example: python validate_handoff.py .claude/handoffs/2024-01-15-auth.md")
        sys.exit(1)

    filepath = sys.argv[1]
    result = validate_handoff(filepath)
    success = print_report(result)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
