"""skills_publish with a fake workspace client: create -> upload -> finalize, idempotent."""

from __future__ import annotations

import io
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from genie_ontology_modeled_knowledge_sdk import skills_publish as sp
from genie_ontology_modeled_knowledge_sdk.config import config_from_dict, validate_config

SDK_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = SDK_ROOT / "skills"
MAPPING = SDK_ROOT / "ci" / "skills.yaml"


class NotFound(Exception):
    pass


class FakeGateway:
    def __init__(self) -> None:
        self.skills: set[str] = set()
        self.calls: list[tuple[str, str]] = []

    def get_skill(self, name: str):
        if name not in self.skills:
            raise NotFound(name)
        return SimpleNamespace(name=name)

    def create_skill(self, parent: str, skill_id: str, skill):
        name = f"skills/{parent.removeprefix('schemas/')}.{skill_id}"
        self.skills.add(name)
        self.calls.append(("create", name))

    def finalize_skill(self, name: str):
        assert name in self.skills
        self.calls.append(("finalize", name))

    def list_skills(self, parent: str):
        prefix = f"skills/{parent.removeprefix('schemas/')}."
        return iter(SimpleNamespace(name=n) for n in sorted(self.skills) if n.startswith(prefix))


class FakeFiles:
    def __init__(self) -> None:
        self.data: dict[str, bytes] = {}
        self.uploads: list[str] = []

    def upload(self, path: str, contents, overwrite: bool = False):
        self.data[path] = contents.read()
        self.uploads.append(path)

    def list_directory_contents(self, directory_path: str):
        d = directory_path.rstrip("/")
        keys = [k for k in self.data if k.startswith(d + "/")]
        if not keys:
            raise NotFound(d)
        out, seen = [], set()
        for k in sorted(keys):
            rest = k[len(d) + 1 :].split("/")
            if len(rest) == 1:
                out.append(SimpleNamespace(path=k, is_directory=False))
            elif rest[0] not in seen:
                seen.add(rest[0])
                out.append(SimpleNamespace(path=f"{d}/{rest[0]}", is_directory=True))
        return iter(out)

    def download(self, file_path: str):
        return SimpleNamespace(contents=io.BytesIO(self.data[file_path]))


class FakeSchemas:
    def __init__(self, existing: set[str]) -> None:
        self.existing = existing
        self.created: list[str] = []

    def get(self, full_name: str):
        if full_name not in self.existing:
            raise NotFound(full_name)

    def create(self, name: str, catalog_name: str):
        self.existing.add(f"{catalog_name}.{name}")
        self.created.append(f"{catalog_name}.{name}")


@pytest.fixture
def ws():
    return SimpleNamespace(ai_gateway=FakeGateway(), files=FakeFiles(), schemas=FakeSchemas({"cat.sch"}))


@pytest.fixture
def mapping():
    return sp.load_mapping(MAPPING, "cat", "sch")


def _copy_skills(tmp_path: Path) -> Path:
    dst = tmp_path / "skills"
    for folder in SKILLS_DIR.iterdir():
        if folder.is_dir() and folder.name.startswith("ontology-"):
            for f in folder.rglob("*"):
                if f.is_file():
                    target = dst / folder.name / f.relative_to(folder)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(f.read_bytes())
    return dst


def test_first_publish_creates_uploads_finalizes(ws, mapping):
    changed = sp.publish(ws, SKILLS_DIR, mapping)
    local_total = sum(len(sp.read_skill_files(SKILLS_DIR / t.folder)) for t in mapping)
    assert set(changed) == {t.skill_id for t in mapping}
    assert sum(len(v) for v in changed.values()) == local_total
    assert all(v for v in changed.values())
    assert len(ws.files.uploads) == local_total
    assert [c for c, _ in ws.ai_gateway.calls].count("create") == 6
    assert [c for c, _ in ws.ai_gateway.calls].count("finalize") == 6
    assert all(p.startswith("/Skills/cat/sch/ontology_") for p in ws.files.uploads)
    assert sp.list_published(ws, "cat", "sch") == sorted(t.fqn for t in mapping)


def test_second_publish_is_a_no_op(ws, mapping):
    sp.publish(ws, SKILLS_DIR, mapping)
    calls, uploads = len(ws.ai_gateway.calls), len(ws.files.uploads)
    changed = sp.publish(ws, SKILLS_DIR, mapping)
    assert all(v == [] for v in changed.values())
    assert len(ws.ai_gateway.calls) == calls
    assert len(ws.files.uploads) == uploads


def test_changed_file_is_the_only_upload(ws, tmp_path):
    skills = _copy_skills(tmp_path)
    mapping = sp.load_mapping(MAPPING, "cat", "sch")
    sp.publish(ws, skills, mapping)
    before = len(ws.files.uploads)
    md = skills / "ontology-tuning" / "SKILL.md"
    md.write_text(md.read_text(encoding="utf-8") + "\nextra\n", encoding="utf-8")
    changed = sp.publish(ws, skills, mapping)
    assert changed["ontology_tuning"] == ["SKILL.md"]
    assert sum(len(v) for k, v in changed.items() if k != "ontology_tuning") == 0
    assert ws.files.uploads[before:] == ["/Skills/cat/sch/ontology_tuning/SKILL.md"]
    assert ws.ai_gateway.calls[-1] == ("finalize", "skills/cat.sch.ontology_tuning")


def test_existing_skill_is_updated_not_duplicated(ws, mapping):
    sp.publish(ws, SKILLS_DIR, mapping)
    ws.ai_gateway.calls.clear()
    ws.files.data = {k: b"old" for k in ws.files.data}
    sp.publish(ws, SKILLS_DIR, mapping)
    assert not [c for c, _ in ws.ai_gateway.calls if c == "create"]
    assert [c for c, _ in ws.ai_gateway.calls].count("finalize") == 6


def test_dry_run_writes_nothing(ws, mapping):
    changed = sp.publish(ws, SKILLS_DIR, mapping, dry_run=True)
    assert all(changed.values())
    assert ws.ai_gateway.calls == [] and ws.files.uploads == []


def test_plan_reports_stale_files(ws, mapping):
    sp.publish(ws, SKILLS_DIR, mapping)
    ws.files.data["/Skills/cat/sch/ontology_deep_eda/references/old.md"] = b"x"
    plan = sp.plan_publish(SKILLS_DIR, mapping, ws)["ontology_deep_eda"]
    assert plan.stale == ["references/old.md"]
    assert plan.changed == []


def test_plan_without_client_marks_all_add(mapping):
    plans = sp.plan_publish(SKILLS_DIR, mapping)
    assert all(not p.exists and p.add and not p.update for p in plans.values())


def test_check_schema_reports_and_never_creates_by_default(ws):
    assert sp.check_schema(ws, "cat", "sch")["exists"] is True
    report = sp.check_schema(ws, "cat", "missing")
    assert report["exists"] is False and report["created"] is False
    assert ws.schemas.created == []
    assert sp.check_schema(ws, "cat", "missing", create_schema=True)["created"] is True
    assert ws.schemas.created == ["cat.missing"]


def test_load_mapping_errors(tmp_path):
    with pytest.raises(ValueError):
        sp.load_mapping(MAPPING, "", "sch")
    bad = tmp_path / "skills.yaml"
    bad.write_text("skills:\n  - source: a/b\n    target: ${SKILLS_CATALOG}.${SKILLS_SCHEMA}.Bad-Id\n", encoding="utf-8")
    with pytest.raises(ValueError, match="snake_case"):
        sp.load_mapping(bad, "c", "s")


def test_cli_check_only(capsys):
    rc = sp.main(["--mapping", str(MAPPING), "--skills-dir", str(SKILLS_DIR), "--catalog", "c", "--schema", "s", "--check-only"])
    assert rc == 0
    assert json.loads(capsys.readouterr().out) == {"errors": []}


def test_sdk_config_skills_key(tpch_config):
    cfg = dict(tpch_config, skills={"catalog": "cat", "schema": "sch", "ids": ["ontology_tuning"]})
    assert validate_config(cfg) == []
    assert config_from_dict(cfg).to_dict()["skills"] == cfg["skills"]
    assert validate_config(dict(tpch_config, skills={"catalog": "cat"}))
    assert validate_config(dict(tpch_config, skills={"catalog": "c", "schema": "s", "ids": ["Bad-Id"]}))


def test_scaffold_records_skills_location(tmp_path, tpch_config):
    from genie_ontology_modeled_knowledge_sdk.scaffold import scaffold_project

    skills = {"catalog": "cat", "schema": "sch", "ids": ["ontology_tuning", "ontology_deep_eda"]}
    target = tmp_path / "proj"
    scaffold_project(dict(tpch_config, skills=skills), target, SDK_ROOT)
    assert json.loads((target / "sdk_config.json").read_text(encoding="utf-8"))["skills"] == skills
    memory = (target / "PROJECT_MEMORY.md").read_text(encoding="utf-8")
    assert "## SDK skills" in memory
    assert "`cat.sch.ontology_tuning`" in memory and "`cat.sch.ontology_deep_eda`" in memory


def test_scaffold_without_skills_adds_no_section(tmp_path, tpch_config):
    from genie_ontology_modeled_knowledge_sdk.scaffold import scaffold_project

    target = tmp_path / "proj"
    scaffold_project(tpch_config, target, SDK_ROOT)
    assert "## SDK skills" not in (target / "PROJECT_MEMORY.md").read_text(encoding="utf-8")
