"""The SDK bundle (databricks.yml + resources/) declares the SDK schema and sdk_wheels volume."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ROOT / "resources"
NEW_SCHEMA_TARGETS = ("dev", "prod")
EXISTING_SCHEMA_TARGET = "prod_existing_schema"
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
HEX_ID = re.compile(r"\b[0-9a-f]{16}\b")


@pytest.fixture(scope="module")
def bundle() -> dict:
    return yaml.safe_load((ROOT / "databricks.yml").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def target_resources() -> dict[str, dict]:
    """Merged ``targets.<t>.resources`` from every resources/*.yml file."""
    merged: dict[str, dict] = {}
    for path in sorted(RESOURCES.glob("*.yml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        assert "resources" not in doc, f"{path.name}: resources are target-scoped (schema modes differ per target)"
        for target, spec in (doc.get("targets") or {}).items():
            for kind, items in (spec.get("resources") or {}).items():
                merged.setdefault(target, {}).setdefault(kind, {}).update(items)
    return merged


def test_bundle_basics(bundle):
    assert bundle["bundle"]["name"] == "genie_ontology_modeled_knowledge_sdk"
    assert bundle["include"] == ["resources/*.yml"]
    variables = bundle["variables"]
    for name in ("sdk_catalog", "sdk_consumer_group", "warehouse_id"):
        assert "default" not in variables[name], f"{name} must be required (no default)"
    assert variables["sdk_schema"]["default"] == "ontology_sdk"


def test_targets(bundle):
    targets = bundle["targets"]
    assert set(targets) == {*NEW_SCHEMA_TARGETS, EXISTING_SCHEMA_TARGET}
    assert targets["dev"]["mode"] == "development" and targets["dev"]["default"] is True
    for name in ("prod", EXISTING_SCHEMA_TARGET):
        assert targets[name]["mode"] == "production"
        assert targets[name]["workspace"]["root_path"].startswith("/Workspace/.bundle/${bundle.name}/")


def test_sync_excludes_non_bundle_folders(bundle):
    excluded = set(bundle["sync"]["exclude"])
    assert {"examples/**", "templates/**", "docs/**"} <= excluded


@pytest.mark.parametrize("target", NEW_SCHEMA_TARGETS)
def test_new_schema_mode_declares_schema_and_volume(target_resources, target):
    res = target_resources[target]
    schema = res["schemas"]["sdk"]
    assert schema["catalog_name"] == "${var.sdk_catalog}"
    assert schema["name"] == "${var.sdk_schema}"
    volume = res["volumes"]["sdk_wheels"]
    assert volume["name"] == "sdk_wheels"
    assert volume["catalog_name"] == "${resources.schemas.sdk.catalog_name}"
    assert volume["schema_name"] == "${resources.schemas.sdk.name}"


def test_prod_grants_consumer_group(target_resources):
    res = target_resources["prod"]
    assert res["schemas"]["sdk"]["grants"] == [{"principal": "${var.sdk_consumer_group}", "privileges": ["USE_SCHEMA"]}]
    assert res["volumes"]["sdk_wheels"]["grants"] == [
        {"principal": "${var.sdk_consumer_group}", "privileges": ["READ_VOLUME"]}
    ]


def test_existing_schema_mode_omits_schema_resource(target_resources):
    res = target_resources[EXISTING_SCHEMA_TARGET]
    assert "schemas" not in res
    volume = res["volumes"]["sdk_wheels"]
    assert volume["catalog_name"] == "${var.sdk_catalog}"
    assert volume["schema_name"] == "${var.sdk_schema}"


def test_no_raw_schema_var_in_new_schema_volume():
    text = (RESOURCES / "sdk_wheels.volume.yml").read_text(encoding="utf-8")
    assert "${var.sdk_schema}" not in text


def test_no_committed_workspace_values():
    paths = [ROOT / "databricks.yml", *sorted(RESOURCES.glob("*.yml"))]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert "host:" not in text, path.name
        assert "/Workspace/Users/" not in text, path.name
        assert not EMAIL.search(text), f"{path.name}: e-mail address"
        assert not HEX_ID.search(text), f"{path.name}: warehouse-id shaped value"
