"""Tests for ``genie_ontology_modeled_knowledge_sdk.targets`` (plan build-1/21, task 3).

The CLI is never called: a fake runner returns canned ``bundle summary -o json`` output.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from genie_ontology_modeled_knowledge_sdk import targets

NOW = datetime(2026, 11, 25, 12, 0, 0, tzinfo=UTC)


def _summary(name: str, catalog: str = "cat_a", warehouse: str | None = "wh123", key: str = "ontology_schema") -> dict:
    variables: dict[str, Any] = {"catalog": {"value": catalog}}
    if warehouse is not None:
        variables["warehouse_id"] = {"default": "", "value": warehouse}
    return {
        "bundle": {"name": "ontology-metric-views", "target": "dev"},
        "resources": {"schemas": {key: {"catalog_name": catalog, "name": name}}, "jobs": {}},
        "variables": variables,
    }


class FakeRunner:
    def __init__(self, out: str) -> None:
        self.out = out
        self.calls: list[tuple[list[str], Path]] = []

    def __call__(self, command: Sequence[str], cwd: Path) -> str:
        self.calls.append((list(command), cwd))
        return self.out


@pytest.fixture()
def bundle_dir(tmp_path: Path) -> Path:
    d = tmp_path / "ontology-metric-views"
    d.mkdir()
    (d / "databricks.yml").write_text("bundle:\n  name: ontology-metric-views\n")
    return d


def test_resolve_dev_prefixed_schema(bundle_dir):
    runner = FakeRunner(json.dumps(_summary("dev_jane_doe_ontology_tpch")))
    data = targets.resolve_target(bundle_dir, "dev", runner=runner, now=NOW)
    assert data == {
        "catalog": "cat_a",
        "schema": "dev_jane_doe_ontology_tpch",
        "warehouse_id": "wh123",
        "source": "bundle_summary",
        "resolved_at": "2026-11-25T12:00:00+00:00",
    }
    assert runner.calls == [(["databricks", "bundle", "summary", "-o", "json", "--target", "dev"], bundle_dir)]


def test_resolve_non_dev_target(bundle_dir):
    runner = FakeRunner(json.dumps(_summary("ontology_tpch", catalog="prd_cat", warehouse="")))
    data = targets.resolve_target(bundle_dir, "prd", runner=runner, extra_args=["--var", "consumer_group=g"])
    assert (data["catalog"], data["schema"]) == ("prd_cat", "ontology_tpch")
    assert data["warehouse_id"] is None  # optional warehouse left empty
    assert runner.calls[0][0][-4:] == ["--target", "prd", "--var", "consumer_group=g"]
    datetime.fromisoformat(data["resolved_at"])  # parses


def test_missing_warehouse_variable_is_null():
    assert targets.target_from_summary(_summary("s", warehouse=None))["warehouse_id"] is None


def test_single_schema_with_other_key():
    assert targets.target_from_summary(_summary("s", key="other"))["schema"] == "s"


@pytest.mark.parametrize(
    "summary, match",
    [
        ({"resources": {}}, "no schema resource 'ontology_schema'"),
        (
            {
                "resources": {
                    "schemas": {"a": {"catalog_name": "c", "name": "x"}, "b": {"catalog_name": "c", "name": "y"}}
                }
            },
            "found: a, b",
        ),
        (_summary("${var.schema_name}"), "not resolved"),
        ({"resources": {"schemas": {"ontology_schema": {"name": "s"}}}}, "catalog_name"),
    ],
)
def test_bad_summaries(summary, match):
    with pytest.raises(ValueError, match=match):
        targets.target_from_summary(summary)


def test_not_json(bundle_dir):
    with pytest.raises(ValueError, match="not JSON"):
        targets.resolve_target(bundle_dir, runner=FakeRunner("Error: no value assigned"))


def test_not_a_bundle(tmp_path):
    with pytest.raises(ValueError, match="databricks.yml"):
        targets.resolve_target(tmp_path, runner=FakeRunner("{}"))


def test_write_resolved_target(tmp_path):
    data = targets.target_from_summary(_summary("dev_x_ontology"), now=NOW)
    out = targets.write_resolved_target(tmp_path / "docs" / "registration" / "resolved_target.json", data)
    assert json.loads(out.read_text()) == data
    assert list(json.loads(out.read_text())) == list(targets.RESOLVED_KEYS)
    with pytest.raises(ValueError, match="missing key"):
        targets.write_resolved_target(tmp_path / "bad.json", {"catalog": "c"})


def test_cli_resolve(bundle_dir, tmp_path, capsys):
    runner = FakeRunner(json.dumps(_summary("dev_jane_doe_ontology")))
    out = tmp_path / "resolved_target.json"
    rc = targets.main(
        ["resolve", "--bundle", str(bundle_dir), "--target", "dev", "--out", str(out), "--var", "consumer_group=g"],
        runner=runner,
    )
    assert rc == 0
    written = json.loads(out.read_text())
    assert written["schema"] == "dev_jane_doe_ontology"
    assert json.loads(capsys.readouterr().out) == written
    assert runner.calls[0][0][-2:] == ["--var", "consumer_group=g"]


def test_cli_error_exit(bundle_dir, capsys):
    def failing(command: Sequence[str], cwd: Path) -> str:
        raise RuntimeError("no value assigned to required variable consumer_group")

    rc = targets.main(["resolve", "--bundle", str(bundle_dir)], runner=failing)
    assert rc == 1
    assert "consumer_group" in capsys.readouterr().err
