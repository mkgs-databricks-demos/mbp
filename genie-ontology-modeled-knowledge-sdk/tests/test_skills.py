"""Skill hygiene (build-1 R1): every SDK skill folder fits the Unity Gateway skill limits."""

from __future__ import annotations

from pathlib import Path

import pytest

from genie_ontology_modeled_knowledge_sdk.skills_publish import (
    MAX_ENTRIES,
    front_matter,
    load_mapping,
    skill_limit_errors,
)

SDK_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = SDK_ROOT / "skills"
MAPPING = SDK_ROOT / "ci" / "skills.yaml"
EXPECTED = {
    "ontology-domain-research",
    "ontology-context-extraction",
    "ontology-deep-eda",
    "ontology-mv-synthesis",
    "ontology-agent-curation",
    "ontology-tuning",
}
SKILL_FOLDERS = sorted(p.name for p in SKILLS_DIR.iterdir() if p.is_dir() and p.name.startswith("ontology-"))


def test_six_skills_present():
    assert set(SKILL_FOLDERS) == EXPECTED


@pytest.mark.parametrize("folder", SKILL_FOLDERS)
def test_skill_within_platform_limits(folder):
    assert skill_limit_errors(SKILLS_DIR / folder) == []


@pytest.mark.parametrize("folder", SKILL_FOLDERS)
def test_front_matter_name_and_description(folder):
    fm = front_matter((SKILLS_DIR / folder / "SKILL.md").read_text(encoding="utf-8"))
    assert fm.get("name") == folder
    assert str(fm.get("description") or "").strip()


def test_mapping_covers_every_skill_with_snake_case_ids():
    targets = load_mapping(MAPPING, "cat", "sch")
    assert {t.folder for t in targets} == EXPECTED
    for t in targets:
        assert t.skill_id == t.folder.replace("-", "_")
        assert t.fqn == f"cat.sch.{t.skill_id}"


def test_mapping_keeps_placeholders():
    text = MAPPING.read_text(encoding="utf-8")
    assert "${SKILLS_CATALOG}.${SKILLS_SCHEMA}." in text


def test_limit_checker_flags_bad_folders(tmp_path):
    bad = tmp_path / "bad-skill"
    deep = bad / "a" / "b" / "c" / "d"
    deep.mkdir(parents=True)
    (bad / "SKILL.md").write_text("---\nname: other\n---\nbody\n", encoding="utf-8")
    (bad / "blob.bin").write_bytes(b"\xff\xfe\x00")
    for i in range(MAX_ENTRIES):
        (bad / f"f{i}.md").write_text("x", encoding="utf-8")
    errors = "\n".join(skill_limit_errors(bad))
    assert "levels deep" in errors
    assert "not a UTF-8 text file" in errors
    assert "files or folders" in errors
    assert "no 'description'" in errors
    assert "differs from the folder name" in errors


def test_limit_checker_missing_skill_md(tmp_path):
    (tmp_path / "empty").mkdir()
    assert skill_limit_errors(tmp_path / "empty") == ["empty: SKILL.md missing"]
