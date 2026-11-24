"""Structure tests for the metric view bundle template (templates/ontology-metric-views).

Static checks only (no CLI, no workspace): the bundle YAML parses, every
``notebook_path`` exists with its extension, the schema is referenced only
through ``${resources.schemas.ontology_schema.*}``, and no workspace hosts or
user names are committed. ``bundle validate --strict`` is run separately.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "ontology-metric-views"
SCHEMA_RESOURCE = TEMPLATE / "resources" / "ontology_schema.yml"
SCHEMA_REF = "${resources.schemas.ontology_schema.name}"
CATALOG_REF = "${resources.schemas.ontology_schema.catalog_name}"
REQUIRED_VARS = {"catalog", "source_catalog", "source_schema", "warehouse_id"}
TASK_KEYS = ["generate_manifest", "register_each_mv", "smoke_test", "cardinality_test"]


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text()) or {}


def _yaml_files() -> list[Path]:
    return [TEMPLATE / "databricks.yml", *sorted((TEMPLATE / "resources").glob("*.yml"))]


def _notebooks() -> list[Path]:
    return sorted((TEMPLATE / "notebooks").glob("*.ipynb"))


def _src(cell: dict) -> str:
    s = cell["source"]
    return s if isinstance(s, str) else "".join(s)


def _title(cell: dict) -> str | None:
    """Cell title from plain metadata, or from Databricks' export metadata."""
    md = cell.get("metadata") or {}
    return md.get("title") or (md.get("application/vnd.databricks.v1+cell") or {}).get("title")


def _walk(node, path=()):
    """Yield (key_path, key, value) for every mapping entry in a parsed YAML tree."""
    if isinstance(node, dict):
        for k, v in node.items():
            yield path + (k,), k, v
            yield from _walk(v, path + (k,))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk(v, path + (i,))


@pytest.fixture(scope="module")
def bundle() -> dict:
    return _load(TEMPLATE / "databricks.yml")


@pytest.fixture(scope="module")
def resources() -> dict:
    merged: dict = {}
    for f in sorted((TEMPLATE / "resources").glob("*.yml")):
        for kind, items in (_load(f).get("resources") or {}).items():
            merged.setdefault(kind, {}).update(items)
    return merged


@pytest.fixture(scope="module")
def job(resources) -> dict:
    return resources["jobs"]["register_metric_views"]


def _tasks(job: dict) -> dict:
    return {t["task_key"]: t for t in job["tasks"]}


# ------------------------------------------------------------------ layout

def test_template_files_exist():
    for rel in [
        "databricks.yml", "resources/ontology_schema.yml", "resources/register_metric_views.job.yml",
        "README.md", ".gitignore", "metric_views/.gitkeep", "tests/README.md",
        "src/genie_ontology_sdk_vendored/README.md",
    ]:
        assert (TEMPLATE / rel).is_file(), rel


def test_gitignore_ignores_bundle_state():
    lines = [ln.strip() for ln in (TEMPLATE / ".gitignore").read_text().splitlines()]
    assert ".databricks/" in lines


def test_vendored_folder_has_only_readme():
    files = [p.name for p in (TEMPLATE / "src" / "genie_ontology_sdk_vendored").iterdir()]
    assert files == ["README.md"]


# ------------------------------------------------------- bundle and targets

def test_bundle_includes_resources(bundle):
    assert bundle["bundle"]["name"] == "ontology-metric-views"
    assert bundle["include"] == ["resources/*.yml"]


def test_variables(bundle):
    variables = bundle["variables"]
    assert set(variables) == REQUIRED_VARS | {"schema_name", "consumer_group"}
    for name in REQUIRED_VARS:
        assert "default" not in variables[name], f"{name} must be required (no default)"
        assert variables[name].get("description")
    assert variables["schema_name"]["default"] == "ontology"
    assert variables["consumer_group"]["default"] == "account users"


def test_targets(bundle):
    targets = bundle["targets"]
    assert set(targets) == {"dev", "prd"}
    dev, prd = targets["dev"], targets["prd"]
    assert dev["mode"] == "development" and dev["default"] is True
    assert set(dev["variables"]) == REQUIRED_VARS
    assert dev["variables"]["source_catalog"] == "samples"
    assert dev["variables"]["source_schema"] == "tpch"
    assert dev["variables"]["warehouse_id"].startswith("<")  # obvious placeholder
    assert prd["mode"] == "production"
    assert prd["workspace"]["root_path"] == "/Workspace/.bundle/${bundle.name}/${bundle.target}"


def test_every_var_reference_is_declared(bundle):
    declared = set(bundle["variables"])
    for f in _yaml_files():
        text = "\n".join(ln for ln in f.read_text().splitlines() if not ln.lstrip().startswith("#"))
        for name in re.findall(r"\$\{var\.([A-Za-z0-9_]+)\}", text):
            assert name in declared, f"{f.name}: undeclared ${{var.{name}}}"


# ---------------------------------------------------------------- resources

def test_schema_resource(resources):
    schema = resources["schemas"]["ontology_schema"]
    assert schema["catalog_name"] == "${var.catalog}"
    assert schema["name"] == "${var.schema_name}"
    grants = schema["grants"]
    assert len(grants) == 1
    assert grants[0]["principal"] == "${var.consumer_group}"
    assert set(grants[0]["privileges"]) == {"USE_SCHEMA", "SELECT"}


def test_job_has_four_tasks(job):
    assert [t["task_key"] for t in job["tasks"]] == TASK_KEYS
    tasks = _tasks(job)
    assert tasks["register_each_mv"]["depends_on"] == [{"task_key": "generate_manifest"}]
    for key in ("smoke_test", "cardinality_test"):
        assert tasks[key]["depends_on"] == [{"task_key": "register_each_mv"}]


def test_for_each_task(job):
    fe = _tasks(job)["register_each_mv"]["for_each_task"]
    assert fe["concurrency"] == 4
    assert fe["inputs"] == "{{tasks.generate_manifest.values.metric_view_list}}"
    inner = fe["task"]
    assert inner["task_key"] == "register_single_mv"
    params = inner["notebook_task"]["base_parameters"]
    assert params["yaml_path"] == "{{input.yaml_path}}"
    assert params["mv_name"] == "{{input.name}}"
    assert params["source_catalog"] == "${var.source_catalog}"
    assert params["source_schema"] == "${var.source_schema}"
    assert params["target_catalog"] == CATALOG_REF
    assert params["target_schema"] == SCHEMA_REF


def test_tests_use_schema_resource(job):
    tasks = _tasks(job)
    for key in ("smoke_test", "cardinality_test"):
        params = tasks[key]["notebook_task"]["base_parameters"]
        assert params["target_catalog"] == CATALOG_REF
        assert params["target_schema"] == SCHEMA_REF


def test_all_tasks_serverless(job):
    compute_keys = {"job_cluster_key", "new_cluster", "existing_cluster_id", "environment_key"}
    assert "job_clusters" not in job
    for t in job["tasks"]:
        for task in (t, t.get("for_each_task", {}).get("task", {})):
            assert not compute_keys & set(task), f"{task.get('task_key')} sets a cluster"
            assert "sql_task" not in task or "warehouse_id" in task["sql_task"]


def test_notebook_paths_exist_with_extension(resources):
    paths = [
        (key_path, v) for key_path, k, v in _walk(resources) if k == "notebook_path"
    ]
    assert len(paths) == 4
    for key_path, rel in paths:
        assert rel.endswith(".ipynb"), f"{key_path}: {rel} must include the .ipynb extension"
        target = (TEMPLATE / "resources" / rel).resolve()
        assert target.is_file(), f"{key_path}: {rel} does not exist"
        assert TEMPLATE in target.parents


# ------------------------------------------------------- conventions / hygiene

def test_no_raw_schema_var_outside_schema_resource():
    files = [f for f in _yaml_files() if f != SCHEMA_RESOURCE] + _notebooks()
    for f in files:
        assert "${var.schema" not in f.read_text(), f"{f.name} references ${{var.schema...}}"


def test_no_hosts_or_user_names(bundle, resources):
    for tree in (bundle, resources):
        for key_path, k, _ in _walk(tree):
            assert k not in {"host", "user_name", "service_principal_name"}, key_path
    host_re = re.compile(r"https?://|cloud\.databricks\.com|azuredatabricks\.net|gcp\.databricks\.com")
    email_re = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    for f in [*_yaml_files(), *_notebooks(), TEMPLATE / "README.md"]:
        text = f.read_text()
        assert not host_re.search(text), f"{f.name} contains a host or URL"
        assert not email_re.search(text), f"{f.name} contains a user name"
        assert "/Users/" not in text, f"{f.name} contains a user workspace path"


# ------------------------------------------------------------------ notebooks

@pytest.mark.parametrize("name", ["generate_manifest", "register_single_mv", "smoke_test", "cardinality_test"])
def test_notebook_structure(name):
    nb = json.loads((TEMPLATE / "notebooks" / f"{name}.ipynb").read_text())
    assert nb["nbformat"] == 4
    code = [c for c in nb["cells"] if c["cell_type"] == "code"]
    src = _src
    first = src(code[0])
    assert first.startswith("%pip install --upgrade databricks-sdk")
    assert "dbutils.library.restartPython()" in first
    assert _title(code[0]) == "Install latest Databricks SDK"
    body = "\n".join(src(c) for c in code)
    assert "dbutils.widgets.text(" in body
    assert "dbutils.notebook.exit(" in src(code[-1])
    for c in code[1:]:
        compile(src(c), f"{name}.ipynb", "exec")  # valid Python (magics only in cell 1)
    # no hardcoded catalogs / schemas: widgets default to empty strings
    assert not re.search(r"dbutils\.widgets\.text\(\s*[^,]+,\s*\"[^\"]+\"", body)
    assert "samples." not in body and "tpch" not in body


def test_generate_manifest_sets_metric_view_list():
    nb = json.loads((TEMPLATE / "notebooks" / "generate_manifest.ipynb").read_text())
    body = "\n".join(_src(c) for c in nb["cells"])
    assert 'taskValues.set(key="metric_view_list"' in body


def test_vendored_loader_imports_sdk(tmp_path):
    """The notebooks' load_sdk cell works against a vendored copy of src/genie_ontology_sdk."""
    import shutil
    import sys

    src_pkg = Path(__file__).resolve().parents[1] / "src" / "genie_ontology_sdk"
    vendored = tmp_path / "src" / "genie_ontology_sdk_vendored"
    vendored.mkdir(parents=True)
    for mod in ("mv_yaml.py", "manifest.py"):
        shutil.copy(src_pkg / mod, vendored / mod)

    nb = json.loads((TEMPLATE / "notebooks" / "register_single_mv.ipynb").read_text())
    loader = next(c for c in nb["cells"] if _title(c) == "Load the vendored SDK library")
    code = _src(loader).replace('load_sdk(args["bundle_root"])', "load_sdk(BUNDLE_ROOT)")

    def is_sdk(name: str) -> bool:
        return name == "genie_ontology_sdk" or name.startswith("genie_ontology_sdk.")

    saved = {k: v for k, v in sys.modules.items() if is_sdk(k)}
    for k in saved:
        del sys.modules[k]
    try:
        ns = {"BUNDLE_ROOT": str(tmp_path)}
        exec(compile(code, "load_sdk", "exec"), ns)
        assert Path(ns["mv_yaml"].__file__).parent == vendored
        assert Path(ns["manifest"].__file__).parent == vendored
        assert callable(ns["mv_yaml"].render_ddl)
    finally:  # restore the real package for the rest of the suite
        for k in [k for k in sys.modules if is_sdk(k)]:
            del sys.modules[k]
        sys.modules.update(saved)
