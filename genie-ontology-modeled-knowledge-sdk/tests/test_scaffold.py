"""Tests for ``genie_ontology_modeled_knowledge_sdk.scaffold`` (plan build-0/09, task 3).

Scaffolds the real SDK templates into ``tmp_path`` and checks the layout, token
rendering, vendored copies, idempotency and the never-overwrite rules.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from genie_ontology_modeled_knowledge_sdk import scaffold
from genie_ontology_modeled_knowledge_sdk.config import validate_config
from genie_ontology_modeled_knowledge_sdk.scaffold import (
    DOCS_DIRS,
    RUN_TOKENS,
    VENDORED_DIR,
    VENDORED_VERSION_FILE,
    ScaffoldReport,
    render_tokens,
    scaffold_project,
)

SDK_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = SDK_ROOT / "templates"

CONFIG = {
    "domain_name": "tpch_supply_chain",
    "domain_context": (
        "TPC-H supply chain: customers place orders for parts supplied by suppliers across nations and regions."
    ),
    "source_tables": [
        f"samples.tpch.{t}"
        for t in ("customer", "orders", "lineitem", "part", "partsupp", "supplier", "nation", "region")
    ],
    "target_catalog": "main",
    "target_schema": "ontology_tpch",
    "max_metric_views_per_agent": 50,
}

RUN_TOKEN_RE = re.compile(r"\{\{\s*(" + "|".join(RUN_TOKENS) + r")\s*\}\}")
# Jobs dynamic value references legitimately stay in the job YAML.
JOBS_REF_RE = re.compile(r"\{\{\s*(tasks|input|job|task|workflow|parent_run|run)\.[^}]*\}\}")


@pytest.fixture()
def project(tmp_path: Path) -> tuple[Path, ScaffoldReport]:
    target = tmp_path / "tpch"
    report = scaffold_project(CONFIG, target, SDK_ROOT)
    return target, report


def _files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*") if p.is_file())


def test_layout(project):
    target, report = project
    assert report.files_written > 0 and not report.skipped and not report.overwritten
    for rel in (
        "sdk_config.json",
        "PROJECT_MEMORY.md",
        "ontology-metric-views/databricks.yml",
        "ontology-metric-views/resources/register_metric_views.job.yml",
        "ontology-metric-views/metric_views/.gitkeep",
        "ontology-genie-agents/databricks.yml",
        "ontology-genie-agents/resources/genie_agents.yml",
        "ontology-genie-agents/agents/.gitkeep",
        "docs/plans/waves.json",
        "docs/plans/INDEX.md",
        "docs/plans/README.md",
    ):
        assert (target / rel).is_file(), rel
    plans = sorted((TEMPLATES / "run" / "plans").glob("*.md"))
    assert plans
    for p in plans:
        assert (target / "docs" / "plans" / "plans" / p.name).is_file()
    for d in DOCS_DIRS:
        assert (target / "docs" / d / ".gitkeep").is_file()
    assert not (target / "docs" / "plans" / "PROJECT_MEMORY.md").exists()


def test_every_plan_file_in_manifest_exists(project):
    target, _ = project
    manifest = json.loads((target / "docs" / "plans" / "waves.json").read_text())
    assert manifest["bundle_target"] == "dev"
    for wave in manifest["waves"]:
        for s in wave["sessions"]:
            assert (target / "docs" / "plans" / s["plan_file"]).is_file(), s["plan_file"]


def test_no_run_tokens_left(project):
    target, _ = project
    for f in _files(target):
        text = f.read_text(encoding="utf-8")
        assert not RUN_TOKEN_RE.search(text), f"{f}: run-kit token left"
        if f.parent == target / VENDORED_DIR and f.suffix == ".py":
            continue  # verbatim Python source (f-strings use {{ }}); see test_vendored_files_identical
        leftover = JOBS_REF_RE.sub("", text)
        assert "{{" not in leftover, f"{f}: unexpected '{{{{' left"


def test_tokens_rendered_with_values(project):
    target, _ = project
    waves = (target / "docs" / "plans" / "waves.json").read_text()
    assert "project tpch" in waves and "tpch_supply_chain" in waves


def test_jobs_references_preserved(project):
    target, _ = project
    rel = Path("ontology-metric-views/resources/register_metric_views.job.yml")
    assert (target / rel).read_bytes() == (TEMPLATES / rel).read_bytes()
    assert "{{input.name}}" in (target / rel).read_text()


@pytest.fixture()
def vendored_project(tmp_path: Path) -> tuple[Path, ScaffoldReport]:
    target = tmp_path / "tpch_vendored"
    report = scaffold_project(CONFIG, target, SDK_ROOT, vendor=True)
    return target, report


def test_default_scaffold_vendors_nothing(project):
    """Wheel first: vendor=False writes no vendored folder at all."""
    target, report = project
    assert not (target / VENDORED_DIR).exists()
    assert not [p for p in report.written if "genie_ontology_modeled_knowledge_sdk_vendored" in p]


def test_default_notebooks_resolve_installed_package(project):
    """Without a vendored folder, the notebooks' load_sdk falls back to the installed package."""
    import sys

    target, _ = project
    nb = json.loads((target / "ontology-metric-views" / "notebooks" / "register_single_mv.ipynb").read_text())

    def _src(c):
        return c["source"] if isinstance(c["source"], str) else "".join(c["source"])

    def _title(c):
        md = c.get("metadata") or {}
        return md.get("title") or (md.get("application/vnd.databricks.v1+cell") or {}).get("title")

    loader = next(c for c in nb["cells"] if _title(c) == "Load the vendored SDK library")
    code = _src(loader).replace('load_sdk(args["bundle_root"])', "load_sdk(BUNDLE_ROOT)")
    import genie_ontology_modeled_knowledge_sdk as pkg

    saved = dict(sys.modules)
    try:
        ns = {"BUNDLE_ROOT": str(target / "ontology-metric-views")}
        exec(compile(code, "load_sdk", "exec"), ns)
        assert Path(ns["mv_yaml"].__file__).parent == Path(pkg.__file__).parent
    finally:
        sys.modules.clear()
        sys.modules.update(saved)


def test_vendored_closure():
    mods = scaffold.vendored_modules(SDK_ROOT)
    # the template notebooks import mv_yaml and manifest; manifest imports mv_yaml
    assert {"mv_yaml.py", "manifest.py"} <= set(mods)
    assert list(mods) == sorted(mods)


def test_vendored_files_identical(vendored_project):
    target, _ = vendored_project
    mods = scaffold.vendored_modules(SDK_ROOT)
    for module in mods:
        dst = target / VENDORED_DIR / module
        # source tree: <sdk>/src/<pkg>; installed wheel (no src/): the installed package
        assert dst.read_bytes() == (scaffold._package_dir(SDK_ROOT) / module).read_bytes()
    # the template README stays next to the vendored copies
    assert (target / VENDORED_DIR / "README.md").is_file()
    from genie_ontology_modeled_knowledge_sdk import __version__

    assert (target / VENDORED_DIR / VENDORED_VERSION_FILE).read_text().strip() == __version__
    # the copies cover their own SDK imports (closed under import)
    pkg_dir = scaffold._package_dir(SDK_ROOT)
    for module in mods:
        refs = scaffold._sdk_module_refs((pkg_dir / module).read_text(), pkg_dir)
        assert refs <= set(mods), module


def test_sdk_config_valid(project):
    target, _ = project
    data = json.loads((target / "sdk_config.json").read_text())
    assert validate_config(data) == []
    assert data["domain_name"] == "tpch_supply_chain"
    assert len(data["source_tables"]) == 8


def test_never_copies_protected_dirs(project):
    target, _ = project
    for f in _files(target):
        parts = f.relative_to(target).parts
        assert ".databricks" not in parts and ".rendered" not in parts, f
        assert "__pycache__" not in parts


def test_second_run_is_idempotent(project):
    target, first = project
    second = scaffold_project(CONFIG, target, SDK_ROOT)
    assert second.files_written == 0
    assert not second.skipped
    assert sorted(second.unchanged) == sorted(first.written)


def test_existing_files_are_skipped(project):
    target, _ = project
    readme = target / "ontology-metric-views" / "README.md"
    readme.write_text("my edits\n")
    report = scaffold_project(CONFIG, target, SDK_ROOT)
    assert report.files_written == 0
    assert report.skipped == ["ontology-metric-views/README.md"]
    assert readme.read_text() == "my edits\n"


def test_force_overwrites_but_not_overrides(project):
    target, _ = project
    readme = target / "ontology-metric-views" / "README.md"
    readme.write_text("my edits\n")
    overrides = target / "ontology-genie-agents" / ".databricks" / "bundle" / "dev" / "variable-overrides.json"
    overrides.parent.mkdir(parents=True)
    overrides.write_text('{"catalog": "secret_catalog"}')
    report = scaffold_project(CONFIG, target, SDK_ROOT, force=True)
    assert report.overwritten == ["ontology-metric-views/README.md"]
    assert readme.read_bytes() == (TEMPLATES / "ontology-metric-views" / "README.md").read_bytes()
    assert overrides.read_text() == '{"catalog": "secret_catalog"}'


def test_existing_overrides_untouched_on_fresh_scaffold(tmp_path):
    target = tmp_path / "proj"
    overrides = target / "ontology-metric-views" / ".databricks" / "bundle" / "dev" / "variable-overrides.json"
    overrides.parent.mkdir(parents=True)
    overrides.write_text("{}")
    report = scaffold_project(CONFIG, target, SDK_ROOT)
    assert overrides.read_text() == "{}"
    assert not any(".databricks" in p for p in report.written)


def test_invalid_config_raises(tmp_path):
    bad = dict(CONFIG)
    del bad["target_catalog"]
    with pytest.raises(ValueError):
        scaffold_project(bad, tmp_path / "x", SDK_ROOT)
    assert not (tmp_path / "x").exists()


def test_bad_sdk_root(tmp_path):
    with pytest.raises(FileNotFoundError):
        scaffold_project(CONFIG, tmp_path / "x", tmp_path / "nope")


def test_placeholder_agent_not_copied(project):
    target, report = project
    for rel in scaffold.PLACEHOLDER_FILES:
        assert (TEMPLATES / rel).is_file(), f"template placeholder moved: {rel}"
        assert not (target / rel).exists(), rel
        assert rel.as_posix() not in report.written
    assert not list((target / "ontology-genie-agents" / "agents").glob("*.geniespace.json"))


def test_schema_name_rendered_from_target_schema(project):
    import yaml

    target, _ = project
    bundle = yaml.safe_load((target / "ontology-metric-views" / "databricks.yml").read_text())
    assert bundle["variables"]["schema_name"]["default"] == CONFIG["target_schema"]
    template = yaml.safe_load((TEMPLATES / "ontology-metric-views" / "databricks.yml").read_text())
    assert template["variables"]["schema_name"]["default"] == "ontology"  # template keeps the generic default
    # Nothing else in the file changes.
    t_lines = (TEMPLATES / "ontology-metric-views" / "databricks.yml").read_text().splitlines()
    p_lines = (target / "ontology-metric-views" / "databricks.yml").read_text().splitlines()
    assert len(t_lines) == len(p_lines)
    diffs = [(a, b) for a, b in zip(t_lines, p_lines, strict=True) if a != b]
    assert [d for d in diffs if "ontology-metric-views" not in d[0]] == [
        ("    default: ontology", f"    default: {CONFIG['target_schema']}")
    ]
    assert len(diffs) == 2  # plus the project-specific bundle name


@pytest.mark.parametrize("bundle", ["ontology-metric-views", "ontology-genie-agents"])
def test_bundle_names_are_project_specific(tmp_path, bundle):
    """Two scaffolded projects never share a bundle name, so never a deployment root or state.

    P1-6 incident (2026-11-27): the child project kept the template name `ontology-metric-views`, shared
    the TPC-H dogfood's `~/.bundle/ontology-metric-views/dev` state, and its deploy renamed TPC-H's schema.
    """
    import yaml

    names = []
    for project_name in ("alpha", "beta"):
        target = tmp_path / project_name
        scaffold_project(CONFIG, target, SDK_ROOT, project_name=project_name)
        name = yaml.safe_load((target / bundle / "databricks.yml").read_text())["bundle"]["name"]
        assert name == f"{project_name}-{bundle}"
        names.append(name)
    assert len(set(names)) == 2
    template = (TEMPLATES / bundle / "databricks.yml").read_text()
    assert f'name: "{{{{project_name}}}}-{bundle}"' in template


def test_render_schema_name_quotes_and_errors():
    text = "variables:\n  schema_name:\n    description: x\n    default: ontology\n  other:\n    default: keep\n"
    out = scaffold.render_schema_name(text, "my-schema")
    assert '    default: "my-schema"' in out and "    default: keep" in out
    with pytest.raises(ValueError, match="schema_name"):
        scaffold.render_schema_name("variables:\n  other:\n    default: x\n", "s")


def test_render_tokens_only_known():
    text = "{{project_name}} {{ domain_name }} {{input.name}} ${var.catalog} {{other}}"
    out = render_tokens(text, {"project_name": "p", "domain_name": "d"})
    assert out == "p d {{input.name}} ${var.catalog} {{other}}"


def test_cli(tmp_path, capsys):
    cfg = tmp_path / "sdk_config.json"
    cfg.write_text(json.dumps(CONFIG))
    target = tmp_path / "cli_proj"
    rc = scaffold.main(["--config", str(cfg), "--target", str(target), "--sdk-root", str(SDK_ROOT)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["files_written"] > 0
    assert (target / "sdk_config.json").is_file()
