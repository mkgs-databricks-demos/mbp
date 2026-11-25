"""Static checks for the Genie Agent bundle template (templates/ontology-genie-agents, DAB 2).

The live check (`bundle validate --strict --target dev` after the render step) is run by
the build gate with the CLI; these tests cover what can be checked without a workspace.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

from genie_ontology_modeled_knowledge_sdk import geniespace

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "templates" / "ontology-genie-agents"
RESOURCES = BUNDLE / "resources"
AGENTS = BUNDLE / "agents"
RENDERED_DIR = ".rendered"
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def _load(path: Path) -> dict:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(doc, dict), f"{path} is not a YAML mapping"
    return doc


def _bundle() -> dict:
    return _load(BUNDLE / "databricks.yml")


def _resource_files() -> list[Path]:
    return sorted(RESOURCES.glob("*.yml"))


def _genie_spaces() -> dict[str, tuple[Path, dict]]:
    spaces: dict[str, tuple[Path, dict]] = {}
    for path in _resource_files():
        for key, spec in ((_load(path).get("resources") or {}).get("genie_spaces") or {}).items():
            assert key not in spaces, f"duplicate genie_spaces key {key}"
            spaces[key] = (path, spec)
    return spaces


def _source_for(yml: Path, file_path: str) -> Path:
    """Pre-render source of a file_path (file_path is relative to the YAML file)."""
    resolved = (yml.parent / file_path).resolve()
    rel = resolved.relative_to(BUNDLE.resolve())
    if rel.parts and rel.parts[0] == RENDERED_DIR:
        return AGENTS / Path(*rel.parts[1:])
    return resolved


def test_yaml_parses():
    _bundle()
    files = _resource_files()
    assert files, "no resources/*.yml"
    for path in files:
        _load(path)


def test_engine_direct_and_includes_resources():
    bundle = _bundle()
    assert bundle["bundle"]["engine"] == "direct"
    assert "resources/*.yml" in bundle.get("include", [])


def test_targets_dev_and_prd():
    targets = _bundle()["targets"]
    assert set(targets) == {"dev", "prd"}
    assert targets["dev"]["mode"] == "development"
    assert targets["dev"].get("default") is True
    assert targets["prd"]["mode"] == "production"
    assert targets["dev"]["variables"]["genie_parent_path"] == "${workspace.root_path}/genie"


def test_variables():
    variables = _bundle()["variables"]
    for name in ("warehouse_id", "catalog", "schema", "consumer_group", "curator_group", "genie_parent_path"):
        assert name in variables, name
        assert variables[name].get("description"), f"{name} has no description"
    assert variables["consumer_group"]["default"] == "account users"
    for required in ("warehouse_id", "catalog", "schema", "curator_group"):
        assert "default" not in variables[required], f"{required} must not have a default"


def test_no_hosts_or_user_names():
    texts = [(BUNDLE / "databricks.yml").read_text(encoding="utf-8")] + [
        p.read_text(encoding="utf-8") for p in _resource_files()
    ]
    for text in texts:
        assert "host:" not in text
        assert "user_name" not in text
        assert "service_principal_name" not in text
        assert not EMAIL.search(text), "e-mail address in bundle YAML"

    def walk(node):
        if isinstance(node, dict):
            assert "host" not in node
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(_bundle())


def test_genie_spaces_resource_shape():
    spaces = _genie_spaces()
    assert "ontology_agent" in spaces
    allowed = {"title", "description", "warehouse_id", "file_path", "serialized_space", "parent_path", "permissions"}
    for key, (_, spec) in spaces.items():
        assert set(spec) <= allowed, f"{key}: unknown keys {set(spec) - allowed}"
        assert spec["warehouse_id"] == "${var.warehouse_id}"
        assert spec["parent_path"] == "${var.genie_parent_path}"
        assert spec.get("title")
        assert spec.get("file_path"), f"{key}: file_path missing"
        grants = {(p["level"], p.get("group_name")) for p in spec["permissions"]}
        assert grants == {("CAN_RUN", "${var.consumer_group}"), ("CAN_EDIT", "${var.curator_group}")}


def test_file_path_sources_exist():
    for key, (yml, spec) in _genie_spaces().items():
        src = _source_for(yml, spec["file_path"])
        assert src.is_file(), f"{key}: source {src} for file_path {spec['file_path']} does not exist"
        assert src.name.endswith(geniespace.SPACE_FILE_SUFFIX)


def test_one_resource_per_agent_file():
    sources = sorted(_source_for(yml, spec["file_path"]).name for yml, spec in _genie_spaces().values())
    files = sorted(p.name for p in AGENTS.glob(f"*{geniespace.SPACE_FILE_SUFFIX}"))
    assert files and sources == files


@pytest.mark.parametrize("path", sorted(AGENTS.glob(f"*{geniespace.SPACE_FILE_SUFFIX}")), ids=lambda p: p.name)
def test_agent_file_tokenized_valid_and_renders(path: Path):
    text = path.read_text(encoding="utf-8")
    doc = json.loads(text)
    assert geniespace.validate_space(doc) == []
    assert "${var." not in text, "bundle variables are not interpolated in file_path JSON; use SDK tokens"
    for table in doc["data_sources"]["tables"]:
        assert table["identifier"].startswith(geniespace.TOKEN_IDENTIFIER_PREFIX + ".")
    rendered = json.loads(geniespace.render_space_text(text, {"catalog": "cat", "schema": "sch", "warehouse_id": "w"}))
    assert geniespace.validate_space(rendered) == []
    assert all(t["identifier"].startswith("cat.sch.") for t in rendered["data_sources"]["tables"])


def test_gitignore():
    lines = {line.strip() for line in (BUNDLE / ".gitignore").read_text(encoding="utf-8").splitlines()}
    assert ".databricks/" in lines
    assert ".rendered/" in lines


def test_readme_records_interpolation_result():
    readme = (BUNDLE / "README.md").read_text(encoding="utf-8")
    assert "Interpolation experiment" in readme
    assert "not interpolated" in readme
    assert re.search(r"CLI v\d+\.\d+\.\d+", readme)
    assert "geniespace render agents .rendered" in readme
    assert "variable-overrides.json" in readme
