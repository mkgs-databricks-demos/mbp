"""Tests for setup_project (build-1 R6): SDK setup, project prerequisites, overrides, vars file.

Fake clients only; every file is written under pytest's tmp_path.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from conftest import FakeNotFound, FakeWorkspaceClient

from genie_ontology_modeled_knowledge_sdk import setup_project as sp

USER = "jane.doe@example.com"
SPN_APP_ID = "72bab3e9-0000-4000-8000-000000000001"
SDK_VOLUME = "/Volumes/cat_a/dev_jane_doe_ontology_sdk/sdk_wheels"
NB = Path(__file__).resolve().parents[1] / "notebooks"


class SetupFakeWorkspace(FakeWorkspaceClient):
    """Adds grants, warehouses, Git folders, skills and Pages to the shared fake."""

    def __init__(self, *, privileges=None, warehouses=None, repos=None, skills=None, grants_error=False,
                 principals=None, **kw):
        super().__init__(**kw)
        # name -> "user" | "Group" (account) | "WorkspaceGroup" | "service_principal"
        known = principals if principals is not None else {
            "readers-acct": "Group", "curators-acct": "Group", "admins": "WorkspaceGroup",
            USER: "user", SPN_APP_ID: "service_principal"}
        self._privs = privileges or {}  # (type, full_name) -> set of privileges
        self._grants_error = grants_error
        whs = warehouses if warehouses is not None else {"wh1": "RUNNING"}
        repo_map = repos or {}  # git folder path -> branch
        skill_list = list(skills or [])
        outer = self

        class _Grants:
            def get_effective(self, securable_type, full_name, principal=None, **_):
                if outer._grants_error:
                    raise PermissionError("cannot read grants")
                privs = outer._privs.get((securable_type, full_name), set())
                return SimpleNamespace(
                    privilege_assignments=[
                        SimpleNamespace(principal=principal, privileges=[SimpleNamespace(privilege=p) for p in privs])
                    ]
                )

        class _Warehouses:
            def get(self, wid):
                if wid not in whs:
                    raise FakeNotFound(f"warehouse {wid} does not exist")
                return SimpleNamespace(id=wid, name=f"wh-{wid}", state=whs[wid])

        ids = {path: i for i, path in enumerate(repo_map, 1)}

        class _Workspace:
            def get_status(self, path):
                if path in ids:
                    return SimpleNamespace(object_type="REPO", object_id=ids[path])
                if any(r.startswith(path + "/") or path.startswith(r + "/") for r in repo_map):
                    return SimpleNamespace(object_type="DIRECTORY", object_id=0)
                raise FakeNotFound(path)

        class _Repos:
            def get(self, rid):
                path = next(p for p, i in ids.items() if i == rid)
                return SimpleNamespace(path=path, branch=repo_map[path])

        class _Gateway:
            def list_skills(self, parent):
                prefix = parent.removeprefix("schemas/") + "."
                return [SimpleNamespace(name=f"skills/{s}") for s in skill_list if s.startswith(prefix)]

        class _Api:
            def do(self, method, path, query=None):
                if 'domains/missing' in str(query):
                    raise FakeNotFound("domain not found")
                return {"pages": []}

        def _lister(kind_ok):
            def _list(filter="", **_):
                name = filter.split('"')[1] if '"' in filter else ""
                kind = known.get(name)
                if kind is None or not kind_ok(kind):
                    return []
                return [SimpleNamespace(meta=SimpleNamespace(resource_type=kind))]
            return SimpleNamespace(list=_list)

        self.service_principals = _lister(lambda k: k == "service_principal")
        self.users = _lister(lambda k: k == "user")
        self.groups = _lister(lambda k: k in ("Group", "WorkspaceGroup"))
        self.grants = _Grants()
        self.warehouses = _Warehouses()
        self.workspace = _Workspace()
        self.repos = _Repos()
        self.ai_gateway = _Gateway()
        self.api_client = _Api()
        self.current_user = SimpleNamespace(me=lambda: SimpleNamespace(user_name=USER))


def _ws(**kw) -> SetupFakeWorkspace:
    base = dict(
        data={"cat_a": {"dev_jane_doe_ontology_sdk": []}},
        privileges={("catalog", "cat_a"): {"CREATE_SCHEMA", "USE_CATALOG"}},
        repos={"/Users/jane.doe@example.com/repo": "jd-genie-feature"},
        skills=[f"cat_a.dev_jane_doe_ontology_sdk.{i}" for i in sp.DEFAULT_SKILL_IDS],
        volume_dirs={f"{SDK_VOLUME}/.internal": ["genie_ontology_modeled_knowledge_sdk-0.1.0-py3-none-any.whl"]},
    )
    base.update(kw)
    return SetupFakeWorkspace(**base)


def _project(tmp_path: Path, **kw) -> dict:
    d = dict(
        project_dir=str(tmp_path / "proj"),
        catalog="cat_a",
        schema_name="ontology_sales",
        warehouse_id="wh1",
        readers="readers-acct, " + SPN_APP_ID,
        curators=["curators-acct"],
        source_catalog="samples",
        source_schema="tpch",
        user_name=USER,
        sdk_volume_path=SDK_VOLUME,
        sdk_version="0.1.0",
        skills_catalog="cat_a",
        skills_schema="dev_jane_doe_ontology_sdk",
        branch="jd-genie-feature",
    )
    d.update(kw)
    return d


def _read(p: Path) -> dict:
    return json.loads(p.read_text())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def test_dev_prefix_and_resolve_schema():
    assert sp.dev_prefix("Jane.Doe-X@example.com") == "dev_jane_doe_x_"
    assert sp.resolve_schema("ontology", "dev", USER) == "dev_jane_doe_ontology"
    assert sp.resolve_schema("ontology", "prd", USER) == "ontology"
    with pytest.raises(ValueError):
        sp.resolve_schema("ontology", "dev", "")


def test_derive_sources():
    assert sp.derive_sources({"source_tables": ["samples.tpch.orders"]}) == ("samples", "tpch")
    assert sp.derive_sources({"source_schemas": ["c.s"], "source_catalog_for_reads": "x"}) == ("x", "s")
    assert sp.derive_sources({"source_catalogs": ["c"]}) == ("c", "")


def test_unknown_inputs_rejected(tmp_path):
    with pytest.raises(ValueError, match="unknown project inputs"):
        sp.write_overrides(tmp_path, {**_project(tmp_path), "bogus": 1})


# ---------------------------------------------------------------------------
# SDK setup
# ---------------------------------------------------------------------------


def test_setup_sdk_new_schema_writes_overrides(tmp_path):
    res = sp.setup_sdk(_ws(), tmp_path, {"catalog": "cat_a", "warehouse_id": "wh1", "user_name": USER})
    assert res.ok, res.to_dict()
    assert res.target == "dev"
    path = tmp_path / ".databricks/bundle/dev/variable-overrides.json"
    assert _read(path) == {"sdk_catalog": "cat_a", "sdk_schema": "ontology_sdk", "warehouse_id": "wh1"}
    assert any("bundle deploy -t dev" in c for c in res.commands)
    assert any("publish_skills" in c for c in res.commands)
    # second run: nothing changes
    again = sp.setup_sdk(_ws(), tmp_path, {"catalog": "cat_a", "warehouse_id": "wh1", "user_name": USER})
    assert again.overrides.action == "unchanged"


def test_setup_sdk_prod_defaults_to_bundle_readers(tmp_path):
    # No readers: the bundle default applies (account users in prod), so no grants in the overrides.
    inputs = {"catalog": "cat_a", "warehouse_id": "wh1", "target": "prod", "user_name": USER}
    res = sp.setup_sdk(_ws(), tmp_path, inputs)
    assert res.ok, res.to_dict()
    assert "sdk_schema_grants" not in _read(tmp_path / ".databricks/bundle/prod/variable-overrides.json")


def test_setup_sdk_readers_become_grant_lists(tmp_path):
    inputs = {"catalog": "cat_a", "warehouse_id": "wh1", "user_name": USER,
              "readers": f"{USER}, readers-acct, {SPN_APP_ID}"}
    res = sp.setup_sdk(_ws(), tmp_path, inputs)
    assert res.ok, res.to_dict()
    data = _read(tmp_path / ".databricks/bundle/dev/variable-overrides.json")
    assert data["sdk_schema_grants"] == [{"principal": p, "privileges": ["USE_SCHEMA"]}
                                         for p in (USER, "readers-acct", SPN_APP_ID)]
    assert data["sdk_volume_grants"][2] == {"principal": SPN_APP_ID, "privileges": ["READ_VOLUME"]}


def test_setup_sdk_rejects_workspace_local_group(tmp_path):
    inputs = {"catalog": "cat_a", "warehouse_id": "wh1", "user_name": USER, "readers": "admins"}
    res = sp.setup_sdk(_ws(), tmp_path, inputs)
    assert not res.ok and res.overrides is None
    bad = [c for c in res.checks if c.name == "principal:admins"]
    assert bad and bad[0].status == sp.ACTION and "account-level" in bad[0].detail


def test_principal_helpers():
    assert sp.parse_principals(" a, b\nb , ,c ") == ["a", "b", "c"]
    assert sp.principal_kind(SPN_APP_ID) == "service_principal"
    assert sp.principal_kind(USER) == "user"
    assert sp.principal_kind("account users") == "group"
    assert sp.agent_permissions([USER, "readers-acct", SPN_APP_ID], ["curators-acct"]) == [
        {"level": "CAN_RUN", "user_name": USER},
        {"level": "CAN_RUN", "group_name": "readers-acct"},
        {"level": "CAN_RUN", "service_principal_name": SPN_APP_ID},
        {"level": "CAN_EDIT", "group_name": "curators-acct"},
    ]
    checks = {c.name: c.status for c in sp.check_principals(_ws(), ["account users", "nobody-group", SPN_APP_ID])}
    assert checks == {"principal:account users": sp.PASS, "principal:nobody-group": sp.ACTION,
                      f"principal:{SPN_APP_ID}": sp.PASS}


def test_setup_sdk_existing_schema_mode(tmp_path):
    ws = _ws(data={"cat_a": {"shared": []}}, privileges={("schema", "cat_a.shared"): {"CREATE_VOLUME"}})
    inputs = {"catalog": "cat_a", "schema": "shared", "schema_mode": "existing", "warehouse_id": "wh1",
              "readers": ["readers-acct"], "user_name": USER}
    res = sp.setup_sdk(ws, tmp_path, inputs)
    assert res.ok, res.to_dict()
    assert res.target == "prod_existing_schema"
    assert _read(tmp_path / ".databricks/bundle/prod_existing_schema/variable-overrides.json") == {
        "sdk_catalog": "cat_a", "sdk_schema": "shared", "warehouse_id": "wh1",
        "sdk_schema_grants": [{"principal": "readers-acct", "privileges": ["USE_SCHEMA"]}],
        "sdk_volume_grants": [{"principal": "readers-acct", "privileges": ["READ_VOLUME"]}]}


def test_setup_sdk_existing_schema_missing(tmp_path):
    inputs = {"catalog": "cat_a", "schema": "nope", "schema_mode": "existing", "warehouse_id": "wh1",
              "user_name": USER}
    res = sp.setup_sdk(_ws(), tmp_path, inputs)
    assert not res.ok and res.overrides is None
    assert not (tmp_path / ".databricks").exists()


def test_setup_sdk_refuses_missing_catalog(tmp_path):
    res = sp.setup_sdk(_ws(), tmp_path, {"catalog": "no_such", "warehouse_id": "wh1", "user_name": USER})
    assert not res.ok
    assert res.overrides is None and res.commands == []
    assert any(c.name == "catalog" and c.status == sp.ACTION for c in res.checks)
    assert not (tmp_path / ".databricks").exists()


def test_setup_sdk_refuses_without_create_schema(tmp_path):
    res = sp.setup_sdk(_ws(privileges={}), tmp_path, {"catalog": "cat_a", "warehouse_id": "wh1", "user_name": USER})
    assert not res.ok and any(c.name == "create_schema" for c in res.checks if c.status == sp.ACTION)
    res = sp.setup_sdk(_ws(grants_error=True), tmp_path, {"catalog": "cat_a", "warehouse_id": "wh1", "user_name": USER})
    assert not res.ok  # unknown grants are reported, not assumed


def test_setup_sdk_mode_target_mismatch(tmp_path):
    res = sp.setup_sdk(_ws(), tmp_path, {"catalog": "cat_a", "warehouse_id": "wh1", "schema_mode": "existing",
                                          "target": "dev"})
    assert not res.ok and "does not fit" in res.checks[0].detail


def test_setup_sdk_keeps_edited_overrides_without_force(tmp_path):
    inputs = {"catalog": "cat_a", "warehouse_id": "wh1", "user_name": USER}
    sp.setup_sdk(_ws(), tmp_path, inputs)
    path = tmp_path / ".databricks/bundle/dev/variable-overrides.json"
    path.write_text(json.dumps({"sdk_catalog": "edited"}))
    res = sp.setup_sdk(_ws(), tmp_path, inputs)
    assert res.overrides.action == "skipped" and not res.ok
    assert _read(path) == {"sdk_catalog": "edited"}
    res = sp.setup_sdk(_ws(), tmp_path, inputs, force=True)
    assert res.overrides.action == "overwritten" and _read(path)["sdk_catalog"] == "cat_a"


# ---------------------------------------------------------------------------
# Project overrides
# ---------------------------------------------------------------------------


def test_write_overrides_both_files_match(tmp_path):
    inputs = _project(tmp_path)
    results = sp.write_overrides(inputs["project_dir"], inputs)
    assert [r.action for r in results] == ["written", "written"]
    root = Path(inputs["project_dir"])
    mv = _read(root / "ontology-metric-views/.databricks/bundle/dev/variable-overrides.json")
    ag = _read(root / "ontology-genie-agents/.databricks/bundle/dev/variable-overrides.json")
    assert mv["catalog"] == ag["catalog"] == "cat_a"
    assert ag["schema"] == "dev_jane_doe_" + mv["schema_name"]
    assert mv["warehouse_id"] == ag["warehouse_id"] == "wh1"
    assert mv["sdk_volume_path"] == SDK_VOLUME and mv["sdk_version"] == "0.1.0"
    assert (mv["source_catalog"], mv["source_schema"]) == ("samples", "tpch")
    assert mv["schema_grants"] == [{"principal": p, "privileges": ["USE_SCHEMA", "SELECT"]}
                                   for p in ("readers-acct", SPN_APP_ID)]
    assert ag["agent_permissions"] == [
        {"level": "CAN_RUN", "group_name": "readers-acct"},
        {"level": "CAN_RUN", "service_principal_name": SPN_APP_ID},
        {"level": "CAN_EDIT", "group_name": "curators-acct"},
    ]


def test_write_overrides_without_readers_keeps_bundle_defaults(tmp_path):
    inputs = _project(tmp_path, readers="", curators="")
    sp.write_overrides(inputs["project_dir"], inputs)
    root = Path(inputs["project_dir"])
    assert "schema_grants" not in _read(root / "ontology-metric-views/.databricks/bundle/dev/variable-overrides.json")
    agents = _read(root / "ontology-genie-agents/.databricks/bundle/dev/variable-overrides.json")
    assert "agent_permissions" not in agents


def test_write_overrides_prod_target_has_no_prefix(tmp_path):
    inputs = _project(tmp_path, bundle_target="prd", user_name="")
    sp.write_overrides(inputs["project_dir"], inputs)
    ag = _read(Path(inputs["project_dir"]) / "ontology-genie-agents/.databricks/bundle/prd/variable-overrides.json")
    assert ag["schema"] == "ontology_sales"


def test_write_overrides_second_run_no_change(tmp_path):
    inputs = _project(tmp_path)
    sp.write_overrides(inputs["project_dir"], inputs)
    files = sorted(Path(inputs["project_dir"]).rglob("variable-overrides.json"))
    before = {f: (f.read_bytes(), f.stat().st_mtime_ns) for f in files}
    again = sp.write_overrides(inputs["project_dir"], inputs)
    assert [r.action for r in again] == ["unchanged", "unchanged"]
    assert {f: (f.read_bytes(), f.stat().st_mtime_ns) for f in files} == before


def test_write_overrides_force(tmp_path):
    inputs = _project(tmp_path)
    sp.write_overrides(inputs["project_dir"], inputs)
    mv = Path(inputs["project_dir"]) / "ontology-metric-views/.databricks/bundle/dev/variable-overrides.json"
    edited = {**_read(mv), "catalog": "hand_edited"}
    mv.write_text(json.dumps(edited))
    kept = sp.write_overrides(inputs["project_dir"], inputs)
    assert [r.action for r in kept] == ["skipped", "unchanged"]
    assert _read(mv)["catalog"] == "hand_edited"
    forced = sp.write_overrides(inputs["project_dir"], inputs, force=True)
    assert [r.action for r in forced] == ["overwritten", "unchanged"]
    assert _read(mv)["catalog"] == "cat_a"


def test_write_overrides_whitespace_edit_is_unchanged(tmp_path):
    inputs = _project(tmp_path)
    sp.write_overrides(inputs["project_dir"], inputs)
    mv = Path(inputs["project_dir"]) / "ontology-metric-views/.databricks/bundle/dev/variable-overrides.json"
    mv.write_text(json.dumps(_read(mv)))  # compact formatting, same values
    assert sp.write_overrides(inputs["project_dir"], inputs)[0].action == "unchanged"


def test_write_overrides_requires_inputs(tmp_path):
    with pytest.raises(ValueError, match="warehouse_id"):
        sp.write_overrides(tmp_path, _project(tmp_path, warehouse_id=""))
    with pytest.raises(ValueError, match="sdk_volume_path"):
        sp.write_overrides(tmp_path, _project(tmp_path, sdk_volume_path=""))
    # vendored projects do not need the wheel location
    res = sp.write_overrides(tmp_path, _project(tmp_path, vendor=True, sdk_volume_path="", sdk_version=""))
    assert "sdk_volume_path" not in res[0].values


def test_missing_project_inputs():
    empty = {"project_dir": "", "catalog": "", "schema_name": "", "warehouse_id": ""}
    assert set(sp.missing_project_inputs(empty)) >= {
        "project_dir", "catalog", "schema_name", "warehouse_id", "user_name",
        "sdk_volume_path", "sdk_version"}


# ---------------------------------------------------------------------------
# Vars file, commands, checklist
# ---------------------------------------------------------------------------


def test_write_vars_file_outside_project(tmp_path):
    inputs = _project(tmp_path)
    vf = tmp_path / "vars" / "build-waves.vars.json"
    r = sp.write_vars_file(vf, inputs)
    assert r.action == "written"
    v = _read(vf)
    assert v["build_root"] == inputs["project_dir"]
    assert v["manifest_path"] == inputs["project_dir"] + "/docs/plans/waves.json"
    assert v["build_branch"] == "jd-genie-feature" and v["instance_suffix"] == "-proj"
    assert (v["skills_catalog"], v["skills_schema"]) == ("cat_a", "dev_jane_doe_ontology_sdk")
    assert sp.write_vars_file(vf, inputs).action == "unchanged"
    with pytest.raises(ValueError, match="outside the project"):
        sp.write_vars_file(Path(inputs["project_dir"]) / "docs/plans/vars.json", inputs)


def test_project_commands_and_checklist(tmp_path):
    inputs = _project(tmp_path, vars_file="/tmp/v.json", genie_build_waves_dir="/gbw")
    cmds = sp.project_commands(inputs)
    assert cmds[0].endswith("ontology-metric-views && databricks bundle validate --strict --target dev")
    assert any("deploy_instance.py --target dev --vars /tmp/v.json" in c for c in cmds)
    assert all("PYTHONPATH" not in c for c in cmds)
    overrides = sp.write_overrides(inputs["project_dir"], inputs)
    text = sp.checklist({"checks": [sp.Check("catalog", sp.PASS, "ok"), sp.Check("skills", sp.ACTION, "publish")],
                         "overrides": overrides, "commands": cmds})
    assert "- [x] catalog" in text and "- [ ] skills" in text
    assert "- [ ] genie-build-waves vars file" in text and "Owner steps" in text


# ---------------------------------------------------------------------------
# Prerequisites
# ---------------------------------------------------------------------------


def _by_name(checks):
    return {c.name: c for c in checks}


def test_check_prereqs_all_pass(tmp_path):
    inputs = _project(tmp_path, project_dir="/Workspace/Users/jane.doe@example.com/repo/proj", pages_domain_id="d1")
    checks = _by_name(sp.check_prereqs(_ws(), inputs))
    assert {n: c.status for n, c in checks.items()} == {
        "catalog": "pass", "warehouse": "pass", "git_folder": "pass", "skills": "pass",
        "pages_domain": "pass", "sdk_wheel": "pass",
        "principal:readers-acct": "pass", f"principal:{SPN_APP_ID}": "pass", "principal:curators-acct": "pass"}


def test_check_prereqs_reports_actions(tmp_path):
    ws = _ws(privileges={}, warehouses={}, repos={"/Users/jane.doe@example.com/repo": "main"},
             skills=["cat_a.dev_jane_doe_ontology_sdk.ontology_tuning"], volume_dirs={}, principals={})
    inputs = _project(tmp_path, project_dir="/Users/jane.doe@example.com/repo/proj", pages_domain_id="missing")
    checks = _by_name(sp.check_prereqs(ws, inputs))
    assert all(c.status == sp.ACTION for c in checks.values()), checks
    assert "CREATE SCHEMA" in checks["catalog"].detail
    assert "'main'" in checks["git_folder"].detail
    assert "ontology_mv_synthesis" in checks["skills"].detail


def test_check_prereqs_not_git_and_vendor_and_no_domain(tmp_path):
    inputs = _project(tmp_path, project_dir="/Users/jane.doe@example.com/elsewhere", vendor=True)
    checks = _by_name(sp.check_prereqs(_ws(), inputs))
    assert checks["git_folder"].status == sp.ACTION
    assert checks["sdk_wheel"].status == sp.SKIP
    assert checks["pages_domain"].status == sp.SKIP


def test_check_prereqs_wrong_branch_and_missing_wheel_version(tmp_path):
    inputs = _project(tmp_path, project_dir="/Users/jane.doe@example.com/repo", branch="other", sdk_version="9.9.9")
    checks = _by_name(sp.check_prereqs(_ws(), inputs))
    assert "expected 'other'" in checks["git_folder"].detail
    assert checks["sdk_wheel"].status == sp.ACTION and "9.9.9" in checks["sdk_wheel"].detail


# ---------------------------------------------------------------------------
# Notebooks
# ---------------------------------------------------------------------------


def _code(nb: Path) -> str:
    cells = json.loads(nb.read_text())["cells"]
    return "\n".join("".join(c["source"]) for c in cells if c["cell_type"] == "code")


REQUIRED_WIDGETS = ("domain_name", "domain_context", "target_catalog", "target_schema", "source_tables",
                    "warehouse_id", "readers", "curators", "target_dir")


def test_init_notebook_required_widgets_empty():
    code = _code(NB / "init_ontology_project.ipynb")
    for name in REQUIRED_WIDGETS:
        assert f'dbutils.widgets.text("{name}", "",' in code, name
    assert 'dbutils.widgets.dropdown("example", "none", ["none", "tpch"]' in code
    assert 'dbutils.widgets.dropdown("vendor", "false", ["false", "true"]' in code
    assert "examples/tpch/sdk_config.json" in code
    assert '"main"' not in code and "samples.tpch" not in code
    assert code.count("sys.path") == 1  # the guarded developer fallback only


def test_setup_sdk_notebook_widgets():
    code = _code(NB / "setup_sdk.ipynb")
    assert 'dbutils.widgets.text("sdk_catalog", "",' in code
    assert 'dbutils.widgets.text("sdk_schema", "ontology_sdk",' in code
    assert 'dbutils.widgets.dropdown("schema_mode", "new", ["new", "existing"]' in code
    assert "sys.path" not in code and '"main"' not in code
