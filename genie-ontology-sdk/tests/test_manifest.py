"""Tests for genie_ontology_sdk.manifest (forEach manifest.json)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from genie_ontology_sdk import manifest
from genie_ontology_sdk.manifest import build_manifest, validate_manifest_json, write_manifest

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "metric_views"
GOOD = FIXTURES / "good"

MV = "version: 1.1\nsource: ${source_catalog}.${source_schema}.t\nmeasures:\n  - name: N\n    expr: COUNT(1)\n    comment: n\n"


def make_bundle(tmp_path: Path, files: dict[str, str]) -> Path:
    """Create <tmp>/bundle/metric_views/<rel> files; returns the metric_views dir."""
    mv_dir = tmp_path / "bundle" / "metric_views"
    for rel, text in files.items():
        p = mv_dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    mv_dir.mkdir(parents=True, exist_ok=True)
    return mv_dir


def test_build_manifest_on_good_fixtures():
    entries = build_manifest(GOOD)
    assert entries == [
        {"name": "mv_sales_returns", "yaml_path": "good/sales/mv_sales_returns.yml", "domain": "sales", "subdomain": "returns"},
        {"name": "mv_sales_revenue", "yaml_path": "good/sales/mv_sales_revenue.yml", "domain": "sales", "subdomain": "revenue"},
        {"name": "mv_tpch_order_lines", "yaml_path": "good/tpch_supply_chain/orders/mv_tpch_order_lines.yml",
         "domain": "tpch_supply_chain", "subdomain": "orders"},
    ]
    assert validate_manifest_json(entries, base_dir=FIXTURES) == []


def test_build_manifest_sorted_relative_posix_paths(tmp_path):
    mv_dir = make_bundle(tmp_path, {
        "zeta/mv_b.yml": MV,
        "alpha/mv_c.yaml": MV,
        "alpha/mv_a.yml": "# subdomain: pricing\n" + MV,
        "alpha/README.md": "not yaml",
    })
    entries = build_manifest(mv_dir)
    assert [e["name"] for e in entries] == ["mv_a", "mv_b", "mv_c"]
    assert [e["yaml_path"] for e in entries] == [
        "metric_views/alpha/mv_a.yml", "metric_views/zeta/mv_b.yml", "metric_views/alpha/mv_c.yaml",
    ]
    assert [e["subdomain"] for e in entries] == ["pricing", None, None]
    assert [e["domain"] for e in entries] == ["alpha", "zeta", "alpha"]
    assert validate_manifest_json(entries, base_dir=mv_dir.parent) == []


def test_build_manifest_comment_beats_folder_subdomain(tmp_path):
    mv_dir = make_bundle(tmp_path, {"d/folder_sub/mv_x.yml": "# subdomain: from_comment\n" + MV})
    assert build_manifest(mv_dir)[0]["subdomain"] == "from_comment"


def test_build_manifest_explicit_bundle_root(tmp_path):
    mv_dir = make_bundle(tmp_path, {"d/mv_x.yml": MV})
    entries = build_manifest(mv_dir, bundle_root=tmp_path)
    assert entries[0]["yaml_path"] == "bundle/metric_views/d/mv_x.yml"
    with pytest.raises(ValueError, match="not inside bundle root"):
        build_manifest(mv_dir, bundle_root=tmp_path / "elsewhere")


def test_build_manifest_rejects_file_outside_domain_folder(tmp_path):
    mv_dir = make_bundle(tmp_path, {"mv_root.yml": MV})
    with pytest.raises(ValueError, match="domain folder"):
        build_manifest(mv_dir)


def test_build_manifest_rejects_duplicate_names(tmp_path):
    mv_dir = make_bundle(tmp_path, {"a/mv_x.yml": MV, "b/mv_x.yml": MV})
    with pytest.raises(ValueError, match="duplicate"):
        build_manifest(mv_dir)


def test_build_manifest_missing_dir(tmp_path):
    with pytest.raises(ValueError):
        build_manifest(tmp_path / "nope")


def test_build_manifest_empty_dir(tmp_path):
    assert build_manifest(make_bundle(tmp_path, {})) == []


@pytest.fixture
def bundle(tmp_path):
    mv_dir = make_bundle(tmp_path, {"d/mv_a.yml": MV, "d/mv_b.yml": MV})
    return mv_dir.parent, build_manifest(mv_dir)


@pytest.mark.parametrize(
    "mutate,expected",
    [
        (lambda e: e.append(dict(e[0])), "duplicate name"),
        (lambda e: e.reverse(), "sorted"),
        (lambda e: e[0].pop("domain"), "missing key"),
        (lambda e: e[0].update(extra=1), "unknown key"),
        (lambda e: e[0].update(yaml_path="/abs/metric_views/d/mv_a.yml"), "relative"),
        (lambda e: e[0].update(yaml_path="../metric_views/d/mv_a.yml"), "relative"),
        (lambda e: e[0].update(yaml_path="metric_views/d/mv_zz.yml"), "does not match name"),
        (lambda e: e[0].update(name="mv_zz", yaml_path="metric_views/d/mv_zz.yml"), "does not exist"),
        (lambda e: e[0].update(subdomain=""), "subdomain"),
        (lambda e: e[0].update(name="bad-name"), "identifier"),
    ],
    ids=["dup", "unsorted", "missing", "extra", "absolute", "dotdot", "stem", "no-file", "subdomain", "name"],
)
def test_validate_manifest_json_problems(bundle, mutate, expected):
    root, entries = bundle
    assert validate_manifest_json(entries, base_dir=root) == []
    mutate(entries)
    problems = validate_manifest_json(entries, base_dir=root)
    assert any(expected in p for p in problems), problems


def test_validate_manifest_json_not_a_list():
    assert validate_manifest_json({"name": "x"}) == ["manifest must be a JSON array"]


def test_write_manifest_round_trip(bundle):
    root, entries = bundle
    out = write_manifest(entries, root / "manifest.json")
    text = out.read_text()
    assert text.endswith("\n")
    assert json.loads(text) == entries


def test_write_manifest_rejects_invalid(bundle):
    root, entries = bundle
    entries.reverse()
    with pytest.raises(ValueError, match="sorted"):
        write_manifest(entries, root / "manifest.json")
    assert not (root / "manifest.json").exists()


def test_manifest_cli_build(tmp_path, capsys):
    mv_dir = make_bundle(tmp_path, {"d/mv_a.yml": MV})
    out = mv_dir.parent / "manifest.json"
    assert manifest.main(["build", str(mv_dir), str(out)]) == 0
    assert json.loads(out.read_text())[0]["yaml_path"] == "metric_views/d/mv_a.yml"
    assert manifest.main(["build", str(tmp_path / "missing"), str(out)]) == 1
