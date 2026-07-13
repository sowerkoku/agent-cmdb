"""
Doc governance tests — prevent the SKILL.md from regressing to L2.1 state.

L2.1 captured the SKILL.md at 1709 lines with the same sections duplicated
nine times. These tests enforce the bounded-file rule from
`docs/governance.md` §11.

If these fail in CI, do NOT bend the limits. Either split by responsibility
(sibling files) or refactor content lower in the stack.
"""

from pathlib import Path

import pytest


# Where the docs live, relative to the repo root
REPO_ROOT = Path(__file__).resolve().parent.parent
HERMES_SKILL = Path.home() / ".hermes" / "skills" / "knowledge-kernel" / "SKILL.md"
REPO_SKILL = REPO_ROOT / "integrations" / "hermes" / "SKILL.md"

DOCS = REPO_ROOT / "docs"
PITFALLS = DOCS / "pitfalls"
PLAYBOOKS = DOCS / "playbooks"
HISTORY = DOCS / "history"


# Hard limits from docs/governance.md §11
LIMITS = {
    "skill": 500,
    "top_md": 500,
    "pitfall": 200,
    "playbook": 400,
}

# Headings that must NEVER be duplicated in the same file.
# This catches the L2.1 "## Project Structure & Governance appears nine
# times" pathology by structural impossibility.
FORBIDDEN_DUPLICATED_HEADINGS = {
    "## Project Structure & Governance",
    "## Overall:",
    "## Why it exists",
}


def _line_count(path: Path) -> int:
    return sum(1 for _ in path.open(encoding="utf-8"))


def _heading_counts(path: Path) -> dict:
    """Return {heading -> count} across the file."""
    counts: dict[str, int] = {}
    for line in path.open(encoding="utf-8"):
        line = line.rstrip()
        for heading in FORBIDDEN_DUPLICATED_HEADINGS:
            if line == heading or line.startswith(heading + " "):
                counts[heading] = counts.get(heading, 0) + 1
                break
    return counts


# ---------- SKILL.md (the product manifest) -----------------------------


@pytest.fixture(scope="module")
def hermes_skill_lines() -> int:
    return _line_count(HERMES_SKILL) if HERMES_SKILL.exists() else _line_count(REPO_SKILL)


def test_skill_under_skill_limit(hermes_skill_lines: int) -> None:
    """SKILL.md must stay inside the 500-line cap until v3.0."""
    assert hermes_skill_lines <= LIMITS["skill"], (
        f"SKILL.md is {hermes_skill_lines} lines "
        f"(limit {LIMITS['skill']}). "
        f"Refusing merge — split into docs/ by responsibility."
    )


def test_skill_two_copies_remain_in_sync() -> None:
    """The two canonical homes of SKILL.md must be byte-identical."""
    if  not HERMES_SKILL.exists():
        pytest.skip("Hermes-side skill copy not present on this host")
    if not REPO_SKILL.exists():
        pytest.skip("Repo-side skill copy not present")
    assert HERMES_SKILL.read_bytes() == REPO_SKILL.read_bytes(), (
        "SKILL.md has drifted between "
        "~/.hermes/skills/knowledge-kernel/SKILL.md and "
        "integrations/hermes/SKILL.md. Copy one to the other before merging."
    )


def test_skill_no_duplicate_top_level_headings() -> None:
    """Structural impossibility test: a heading must NOT repeat."""
    target = HERMES_SKILL if HERMES_SKILL.exists() else REPO_SKILL
    counts = _heading_counts(target)
    for heading, count in counts.items():
        assert count <= 1, (
            f'{heading!r} appears {count} times in {target} — this is the '
            f"exact pathology that produced the 1709-line L2.1 SKILL.md. "
            f"Refactor to a sibling file instead."
        )


# ---------- docs/ topic files ------------------------------------------


@pytest.mark.parametrize("file_path", sorted(DOCS.glob("*.md")))
def test_doc_topic_under_cap(file_path: Path) -> None:
    """Each top-level topic must not exceed 500 lines."""
    assert _line_count(file_path) <= LIMITS["top_md"], (
        f"{file_path.relative_to(REPO_ROOT)} is over the cap "
        f"({LIMITS['top_md']} lines)."
    )


# ---------- docs/pitfalls/ — one file per pitfall, each small ----------


@pytest.mark.parametrize("file_path", sorted(PITFALLS.glob("*.md")))
def test_pitfall_under_cap(file_path: Path) -> None:
    """Each pitfall is small on purpose; split further if exceeded."""
    assert _line_count(file_path) <= LIMITS["pitfall"], (
        f"{file_path.relative_to(REPO_ROOT)} is over the pitfall cap "
        f"({LIMITS['pitfall']} lines)."
    )


# ---------- docs/playbooks/ -------------------------------------------


@pytest.mark.parametrize("file_path", sorted(PLAYBOOKS.glob("*.md")))
def test_playbook_under_cap(file_path: Path) -> None:
    """A playbook is a recipe — long recipes split into sub-flows."""
    assert _line_count(file_path) <= LIMITS["playbook"], (
        f"{file_path.relative_to(REPO_ROOT)} is over the playbook cap "
        f"({LIMITS['playbook']} lines)."
    )


# ---------- docs/history/ — historical, no cap --------------------------


def test_history_paths_exist() -> None:
    """history/ is allowed unlimited size; just verify it lives where it
    should."""
    assert HISTORY.exists(), "docs/history/ is missing — docs layout broken"


# ---------- One Responsibility, One Canonical Home ---------------------


def test_no_dual_maintenance_of_skill_in_third_place() -> None:
    """There must be exactly TWO copies of SKILL.md: hermes + repo."""
    candidates = [
        HERMES_SKILL if HERMES_SKILL.exists() else None,
        REPO_SKILL if REPO_SKILL.exists() else None,
    ]
    paths = [p for p in candidates if p is not None]
    for stale in [REPO_ROOT / "docs" / "SKILL.md",
                  REPO_ROOT / "SKILL.md",
                  REPO_ROOT / "docs" / "knowledge-kernel.md"]:
        assert not stale.exists(), (
            f"Found stale SKILL.md copy at {stale.relative_to(REPO_ROOT)}. "
            f"Two copies is the maximum, single source of truth is the rule."
        )
