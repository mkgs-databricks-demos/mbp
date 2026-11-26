"""Guided setup for the Genie Ontology Modeled Knowledge SDK (build-1 R6, R7a).

Two steps, each driven by a notebook:

1. **SDK setup** (``notebooks/setup_sdk``, once per workspace): ``setup_sdk``
   checks the catalog and schema the SDK should use (a **new** schema the SDK
   bundle creates is recommended, default ``ontology_sdk``), writes the SDK
   bundle's gitignored ``.databricks/bundle/<target>/variable-overrides.json``
   and returns the exact deploy and skills publishing commands.
2. **Project setup** (``notebooks/init_ontology_project``, once per project):
   ``check_prereqs`` reports each prerequisite as pass / action needed,
   ``write_overrides`` writes both project bundles' overrides files from the
   same inputs, ``write_vars_file`` writes the genie-build-waves instance vars
   file (outside the repository), and ``checklist`` summarises what is done.

This module never deploys, grants or creates Unity Catalog objects. Files are
never overwritten when they differ unless ``force=True`` (re-running with the
same inputs changes nothing). It imports only the standard library at module
level, so ``notebooks/setup_sdk`` can load it from an SDK checkout before the
wheel is published.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any

DEFAULT_SDK_SCHEMA = "ontology_sdk"
SDK_SCHEMA_MODES = ("new", "existing")
# SDK bundle targets (databricks.yml at the SDK root) per schema mode.
SDK_TARGETS = {"new": ("dev", "prod"), "existing": ("prod_existing_schema",)}
# Targets of the project bundles that run in development mode (schema names get the dev prefix).
DEV_MODE_TARGETS = frozenset({"dev"})

MV_BUNDLE = "ontology-metric-views"
AGENTS_BUNDLE = "ontology-genie-agents"
OVERRIDES_FILE = "variable-overrides.json"
WHEEL_NAME = "genie_ontology_modeled_knowledge_sdk-{version}-py3-none-any.whl"
DEFAULT_WHEEL_SUBPATH = ".internal"  # stable CLI upload path (docs/distribution/wheel_publish.md)

# The six SDK skills (ci/skills.yaml ids).
DEFAULT_SKILL_IDS = (
    "ontology_agent_curation",
    "ontology_context_extraction",
    "ontology_deep_eda",
    "ontology_domain_research",
    "ontology_mv_synthesis",
    "ontology_tuning",
)

PASS, ACTION, SKIP = "pass", "action", "skip"
_CREATE_SCHEMA_PRIVS = frozenset({"CREATE_SCHEMA", "ALL_PRIVILEGES"})
_SCHEMA_WRITE_PRIVS = frozenset({"CREATE_VOLUME", "ALL_PRIVILEGES"})
_PROTECTED_BRANCHES = frozenset({"main", "master"})


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class Check:
    """One prerequisite: ``status`` is ``pass``, ``action`` (owner must act) or ``skip``."""

    name: str
    status: str
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.status != ACTION

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass
class WriteResult:
    """Outcome of writing one JSON file: ``written``, ``unchanged``, ``overwritten`` or ``skipped``."""

    path: str
    action: str
    values: dict[str, Any] = field(default_factory=dict)

    @property
    def changed(self) -> bool:
        return self.action in ("written", "overwritten")

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "action": self.action, "values": dict(self.values)}


@dataclass
class SdkSetupResult:
    """Outcome of ``setup_sdk``. ``overrides`` is ``None`` when a check failed."""

    checks: list[Check]
    overrides: WriteResult | None
    target: str
    commands: list[str]

    @property
    def ok(self) -> bool:
        return self.overrides is not None and all(c.ok for c in self.checks)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "target": self.target,
            "checks": [c.to_dict() for c in self.checks],
            "overrides": None if self.overrides is None else self.overrides.to_dict(),
            "commands": list(self.commands),
        }


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------


@dataclass
class SdkSetupInputs:
    """Answers to the SDK setup questions (R7a item 0).

    ``schema_mode`` ``new`` (recommended): the SDK bundle creates ``schema``
    (dev-prefixed in the ``dev`` target). ``existing``: ``schema`` already
    exists and the bundle only adds the ``sdk_wheels`` volume (target
    ``prod_existing_schema``).
    """

    catalog: str
    schema: str = DEFAULT_SDK_SCHEMA
    schema_mode: str = "new"
    consumer_group: str = ""
    warehouse_id: str = ""
    target: str = ""  # default: dev (new) / prod_existing_schema (existing)
    user_name: str = ""  # used for the dev schema prefix; default: ws.current_user.me()

    def resolved_target(self) -> str:
        return self.target or SDK_TARGETS.get(self.schema_mode, ("",))[0]


@dataclass
class ProjectInputs:
    """Inputs for one project's overrides, prerequisite checks and vars file.

    ``schema_name`` is the metric-view bundle's ``schema_name`` (the scaffold
    renders it from ``sdk_config.target_schema``). In a development-mode target
    (``dev``) the deployed schema is ``dev_<user>_<schema_name>``; that
    resolved name is what the agents bundle ``schema`` must be.
    """

    project_dir: str
    catalog: str
    schema_name: str
    warehouse_id: str
    consumer_group: str
    curator_group: str
    source_catalog: str = ""
    source_schema: str = ""
    bundle_target: str = "dev"
    user_name: str = ""
    vendor: bool = False
    sdk_volume_path: str = ""
    sdk_version: str = ""
    sdk_wheel_subpath: str = DEFAULT_WHEEL_SUBPATH
    skills_catalog: str = ""
    skills_schema: str = ""
    skill_ids: list[str] = field(default_factory=lambda: list(DEFAULT_SKILL_IDS))
    pages_domain_id: str = ""
    # genie-build-waves instance
    project_name: str = ""
    branch: str = ""
    instance_suffix: str = ""
    vars_file: str = ""
    genie_build_waves_dir: str = ""

    def resolved_schema(self) -> str:
        return resolve_schema(self.schema_name, self.bundle_target, self.user_name)

    def wheel_path(self) -> str:
        if not (self.sdk_volume_path and self.sdk_version):
            return ""
        sub = self.sdk_wheel_subpath.strip("/")
        base = self.sdk_volume_path.rstrip("/")
        name = WHEEL_NAME.format(version=self.sdk_version)
        return f"{base}/{sub}/{name}" if sub else f"{base}/{name}"


def _as_project_inputs(inputs: ProjectInputs | dict[str, Any]) -> ProjectInputs:
    if isinstance(inputs, ProjectInputs):
        return inputs
    known = {f.name for f in fields(ProjectInputs)}
    unknown = sorted(set(inputs) - known)
    if unknown:
        raise ValueError(f"unknown project inputs: {', '.join(unknown)}")
    return ProjectInputs(**inputs)


def _as_sdk_inputs(inputs: SdkSetupInputs | dict[str, Any]) -> SdkSetupInputs:
    if isinstance(inputs, SdkSetupInputs):
        return inputs
    known = {f.name for f in fields(SdkSetupInputs)}
    unknown = sorted(set(inputs) - known)
    if unknown:
        raise ValueError(f"unknown SDK setup inputs: {', '.join(unknown)}")
    return SdkSetupInputs(**inputs)


def missing_project_inputs(inputs: ProjectInputs | dict[str, Any], *, for_vars_file: bool = False) -> list[str]:
    """Names of required project inputs that are empty (the notebook stops until none are)."""
    p = _as_project_inputs(inputs)
    required = ["project_dir", "catalog", "schema_name", "warehouse_id", "consumer_group", "curator_group"]
    if p.bundle_target in DEV_MODE_TARGETS:
        required.append("user_name")
    if not p.vendor:
        required += ["sdk_volume_path", "sdk_version"]
    if for_vars_file:
        required += ["vars_file", "branch", "skills_catalog", "skills_schema"]
    return [k for k in required if not str(getattr(p, k) or "").strip()]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def dev_prefix(user_name: str) -> str:
    """``dev_<short_name>_``, the schema prefix bundles add in development mode.

    ``short_name`` is the part of the user name before ``@`` with every
    non-alphanumeric character replaced by ``_`` (lowercase).
    """
    short = re.sub(r"[^a-z0-9]", "_", user_name.split("@", 1)[0].strip().lower())
    if not short:
        raise ValueError("user_name is required for the development-mode schema prefix")
    return f"dev_{short}_"


def resolve_schema(schema_name: str, bundle_target: str, user_name: str = "") -> str:
    """Schema name a bundle deploys for ``bundle_target`` (dev prefix in development mode)."""
    if bundle_target in DEV_MODE_TARGETS:
        return dev_prefix(user_name) + schema_name
    return schema_name


def derive_sources(cfg: Any) -> tuple[str, str]:
    """``(source_catalog, source_schema)`` for the metric-view bundle from an ``sdk_config``.

    ``source_catalog_for_reads`` / ``source_schema_for_reads`` win; otherwise
    the first ``source_tables`` / ``source_schemas`` entry. Empty when unknown.
    """
    d = cfg if isinstance(cfg, dict) else cfg.to_dict()
    cat, sch = d.get("source_catalog_for_reads") or "", d.get("source_schema_for_reads") or ""
    first = (d.get("source_tables") or d.get("source_schemas") or [""])[0].split(".")
    if len(first) >= 2:
        cat = cat or first[0]
        sch = sch or first[1]
    elif d.get("source_catalogs"):
        cat = cat or d["source_catalogs"][0]
    return cat, sch


def _text(v: Any) -> str:
    v = getattr(v, "value", v)
    return "" if v is None else str(v)


def _err(e: Exception) -> str:
    return f"{type(e).__name__}: {e}"


def _is_not_found(e: Exception) -> bool:
    return "NotFound" in type(e).__name__ or "does not exist" in str(e).lower() or "not found" in str(e).lower()


def _current_user(ws: Any, given: str) -> str:
    if given:
        return given
    try:
        return _text(ws.current_user.me().user_name)
    except Exception:  # noqa: BLE001 - reported by the caller as a missing input
        return ""


def effective_privileges(ws: Any, securable_type: str, full_name: str, principal: str) -> set[str] | None:
    """Privileges ``principal`` holds on a securable (inherited included); ``None`` if unknown."""
    try:
        resp = ws.grants.get_effective(securable_type=securable_type, full_name=full_name, principal=principal)
    except Exception:  # noqa: BLE001 - API missing or no permission to read grants
        return None
    out: set[str] = set()
    for a in getattr(resp, "privilege_assignments", None) or []:
        for p in getattr(a, "privileges", None) or []:
            out.add(_text(getattr(p, "privilege", p)).upper())
    return out


def _can(ws: Any, securable_type: str, full_name: str, owner: str, user: str, privs: frozenset[str]) -> bool | None:
    if user and owner and owner == user:
        return True
    got = effective_privileges(ws, securable_type, full_name, user) if user else None
    if got is None:
        return None
    return bool(got & privs)


def write_json(path: str | Path, values: dict[str, Any], *, force: bool = False) -> WriteResult:
    """Write ``values`` as JSON unless the file already holds them.

    An existing file with different content (parsed JSON compared, so
    whitespace edits do not count) is kept unless ``force``.
    """
    p = Path(path)
    text = json.dumps(values, indent=2) + "\n"
    if p.exists():
        try:
            current = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            current = None
        if current == values:
            return WriteResult(str(p), "unchanged", values)
        if not force:
            return WriteResult(str(p), "skipped", current if isinstance(current, dict) else {})
        p.write_text(text, encoding="utf-8")
        return WriteResult(str(p), "overwritten", values)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return WriteResult(str(p), "written", values)


def overrides_path(bundle_dir: str | Path, target: str) -> Path:
    """``<bundle_dir>/.databricks/bundle/<target>/variable-overrides.json`` (gitignored)."""
    return Path(bundle_dir) / ".databricks" / "bundle" / target / OVERRIDES_FILE


# ---------------------------------------------------------------------------
# 1. SDK setup (once per workspace)
# ---------------------------------------------------------------------------


def sdk_overrides(inputs: SdkSetupInputs | dict[str, Any]) -> dict[str, str]:
    """Values of the SDK bundle's ``variable-overrides.json``."""
    s = _as_sdk_inputs(inputs)
    out = {"sdk_catalog": s.catalog, "sdk_schema": s.schema, "warehouse_id": s.warehouse_id}
    if s.consumer_group:
        out["sdk_consumer_group"] = s.consumer_group
    return out


def check_sdk_setup(ws: Any, inputs: SdkSetupInputs | dict[str, Any]) -> list[Check]:
    """Checks for SDK setup: inputs, catalog, schema permission, warehouse."""
    s = _as_sdk_inputs(inputs)
    checks: list[Check] = []
    target = s.resolved_target()
    missing = [k for k in ("catalog", "schema", "warehouse_id") if not str(getattr(s, k) or "").strip()]
    if s.schema_mode not in SDK_SCHEMA_MODES:
        checks.append(Check("inputs", ACTION, f"schema_mode must be one of {', '.join(SDK_SCHEMA_MODES)}"))
        return checks
    if target not in SDK_TARGETS[s.schema_mode]:
        checks.append(
            Check("inputs", ACTION, f"target '{target}' does not fit schema_mode '{s.schema_mode}' "
                  f"(use {' or '.join(SDK_TARGETS[s.schema_mode])})")
        )
        return checks
    if target != "dev" and not s.consumer_group:
        missing.append("consumer_group")
    if missing:
        checks.append(Check("inputs", ACTION, "missing: " + ", ".join(missing)))
        return checks
    checks.append(Check("inputs", PASS, f"schema_mode={s.schema_mode}, target={target}"))

    user = _current_user(ws, s.user_name)
    try:
        cat = ws.catalogs.get(s.catalog)
        checks.append(Check("catalog", PASS, f"catalog '{s.catalog}' exists"))
    except Exception as e:  # noqa: BLE001
        checks.append(Check("catalog", ACTION, f"catalog '{s.catalog}' is not accessible ({_err(e)})"))
        return checks

    if s.schema_mode == "new":
        schema = resolve_schema(s.schema, target, user) if target in DEV_MODE_TARGETS and user else s.schema
        can = _can(ws, "catalog", s.catalog, _text(getattr(cat, "owner", "")), user, _CREATE_SCHEMA_PRIVS)
        if can is False:
            checks.append(Check("create_schema", ACTION, f"{user or 'you'} lacks CREATE SCHEMA on '{s.catalog}'"))
        elif can is None:
            checks.append(
                Check("create_schema", ACTION, f"could not read grants on '{s.catalog}': confirm CREATE SCHEMA")
            )
        else:
            checks.append(Check("create_schema", PASS, f"can create '{s.catalog}.{schema}'"))
    else:
        full = f"{s.catalog}.{s.schema}"
        try:
            sch = ws.schemas.get(full)
        except Exception as e:  # noqa: BLE001
            checks.append(Check("schema", ACTION, f"existing schema '{full}' is not accessible ({_err(e)})"))
            return checks
        can = _can(ws, "schema", full, _text(getattr(sch, "owner", "")), user, _SCHEMA_WRITE_PRIVS)
        if can is False:
            checks.append(Check("schema", ACTION, f"{user or 'you'} lacks CREATE VOLUME on '{full}'"))
        elif can is None:
            checks.append(Check("schema", ACTION, f"could not read grants on '{full}': confirm CREATE VOLUME"))
        else:
            checks.append(Check("schema", PASS, f"'{full}' exists and you can create the sdk_wheels volume"))

    checks.append(_check_warehouse(ws, s.warehouse_id))
    return checks


def sdk_commands(sdk_root: str | Path, inputs: SdkSetupInputs | dict[str, Any]) -> list[str]:
    """Exact SDK deploy and skills publishing steps for the chosen target."""
    s = _as_sdk_inputs(inputs)
    t = s.resolved_target()
    root = str(sdk_root)
    return [
        f"cd {root} && databricks bundle validate --strict -t {t}",
        f"cd {root} && databricks bundle deploy -t {t}",
        f"cd {root} && databricks bundle run sdk_smoke -t {t}",
        f"cd {root} && databricks bundle summary -t {t}  # note the resolved SDK schema and sdk_wheels volume path",
        "Publish the skills: run notebooks/publish_skills with skills_catalog = "
        f"{s.catalog} and skills_schema = the resolved SDK schema from bundle summary",
    ]


def setup_sdk(
    ws: Any, sdk_root: str | Path, inputs: SdkSetupInputs | dict[str, Any], *, force: bool = False
) -> SdkSetupResult:
    """Check the SDK setup answers and write the SDK bundle's overrides file.

    Writes nothing when any check needs action (for example a missing catalog).
    Never deploys; the returned ``commands`` are for the owner to run.
    """
    s = _as_sdk_inputs(inputs)
    checks = check_sdk_setup(ws, s)
    target = s.resolved_target()
    if not all(c.ok for c in checks):
        return SdkSetupResult(checks, None, target, [])
    result = write_json(overrides_path(sdk_root, target), sdk_overrides(s), force=force)
    if result.action == "skipped":
        checks.append(Check("overrides", ACTION, f"{result.path} was edited; re-run with force to replace it"))
    return SdkSetupResult(checks, result, target, sdk_commands(sdk_root, s))


# ---------------------------------------------------------------------------
# 2. Project setup
# ---------------------------------------------------------------------------


def _check_warehouse(ws: Any, warehouse_id: str) -> Check:
    if not warehouse_id:
        return Check("warehouse", ACTION, "warehouse_id is empty")
    try:
        wh = ws.warehouses.get(warehouse_id)
    except Exception as e:  # noqa: BLE001
        return Check("warehouse", ACTION, f"warehouse '{warehouse_id}' is not usable ({_err(e)})")
    state = _text(getattr(wh, "state", "")) or "unknown"
    if state in ("DELETED", "DELETING"):
        return Check("warehouse", ACTION, f"warehouse '{warehouse_id}' is {state}")
    return Check("warehouse", PASS, f"warehouse '{getattr(wh, 'name', warehouse_id)}' ({state})")


def _git_folder(ws: Any, path: str) -> tuple[str, str] | None:
    """``(git folder path, branch)`` of the Git folder holding ``path``, or ``None``."""
    p = Path(path.removeprefix("/Workspace") if path.startswith("/Workspace/") else path)
    for cand in (p, *p.parents):
        if str(cand) in ("/", "."):
            break
        try:
            st = ws.workspace.get_status(str(cand))
        except Exception:  # noqa: BLE001 - path does not exist yet: try its parent
            continue
        if _text(getattr(st, "object_type", "")).upper() == "REPO":
            repo = ws.repos.get(int(st.object_id))
            return str(cand), _text(getattr(repo, "branch", ""))
    return None


def check_prereqs(ws: Any, inputs: ProjectInputs | dict[str, Any]) -> list[Check]:
    """Project prerequisites, each ``pass``, ``action`` or ``skip`` (read-only).

    Catalog access and CREATE SCHEMA, warehouse, Git folder on a non-``main``
    branch, the skills schema and the six skills, the Pages domain (if set) and,
    in wheel mode, the SDK wheel for ``sdk_version`` at its stable path.
    """
    p = _as_project_inputs(inputs)
    checks: list[Check] = []
    user = _current_user(ws, p.user_name)

    # Catalog + CREATE SCHEMA
    if not p.catalog:
        checks.append(Check("catalog", ACTION, "catalog is empty"))
    else:
        try:
            cat = ws.catalogs.get(p.catalog)
            can = _can(ws, "catalog", p.catalog, _text(getattr(cat, "owner", "")), user, _CREATE_SCHEMA_PRIVS)
            if can is True:
                checks.append(Check("catalog", PASS, f"'{p.catalog}' accessible, CREATE SCHEMA held"))
            elif can is False:
                checks.append(Check("catalog", ACTION, f"{user or 'you'} lacks CREATE SCHEMA on '{p.catalog}'"))
            else:
                checks.append(
                    Check("catalog", ACTION, f"'{p.catalog}' accessible; could not read grants, confirm CREATE SCHEMA")
                )
        except Exception as e:  # noqa: BLE001
            checks.append(Check("catalog", ACTION, f"catalog '{p.catalog}' is not accessible ({_err(e)})"))

    checks.append(_check_warehouse(ws, p.warehouse_id))

    # Git folder on a feature branch
    try:
        git = _git_folder(ws, p.project_dir) if p.project_dir else None
    except Exception as e:  # noqa: BLE001
        git, git_err = None, _err(e)
    else:
        git_err = ""
    if git is None:
        checks.append(Check("git_folder", ACTION, f"'{p.project_dir}' is not inside a Git folder {git_err}".strip()))
    elif git[1] in _PROTECTED_BRANCHES or not git[1]:
        checks.append(
            Check("git_folder", ACTION, f"Git folder {git[0]} is on '{git[1] or '?'}': switch to a feature branch")
        )
    elif p.branch and git[1] != p.branch:
        checks.append(Check("git_folder", ACTION, f"Git folder {git[0]} is on '{git[1]}', expected '{p.branch}'"))
    else:
        checks.append(Check("git_folder", PASS, f"Git folder {git[0]} on '{git[1]}'"))

    # Skills schema + skills
    if not (p.skills_catalog and p.skills_schema):
        checks.append(
            Check("skills", ACTION, "skills_catalog / skills_schema are empty (the SDK schema from SDK setup)")
        )
    else:
        full = f"{p.skills_catalog}.{p.skills_schema}"
        try:
            ws.schemas.get(full)
            from genie_ontology_modeled_knowledge_sdk.skills_publish import list_published

            published = set(list_published(ws, p.skills_catalog, p.skills_schema))
            want = {f"{full}.{i}" for i in p.skill_ids}
            missing = sorted(want - published)
            if missing:
                detail = "not published: " + ", ".join(missing) + " (run notebooks/publish_skills)"
                checks.append(Check("skills", ACTION, detail))
            else:
                checks.append(Check("skills", PASS, f"{len(want)} skills in {full}"))
        except Exception as e:  # noqa: BLE001
            checks.append(Check("skills", ACTION, f"skills schema '{full}' not readable ({_err(e)})"))

    # Pages domain
    if not p.pages_domain_id:
        checks.append(Check("pages_domain", SKIP, "no Pages domain set: the Pages wave publishes later (dry run only)"))
    else:
        dom = p.pages_domain_id if p.pages_domain_id.startswith("domains/") else f"domains/{p.pages_domain_id}"
        try:
            ws.api_client.do("GET", "/api/2.0/knowledge/pages", query={"page_size": 1, "filter": f'domain = "{dom}"'})
            checks.append(Check("pages_domain", PASS, f"{dom} readable"))
        except Exception as e:  # noqa: BLE001
            checks.append(Check("pages_domain", ACTION, f"{dom} not readable ({_err(e)})"))

    # SDK wheel (wheel mode)
    if p.vendor:
        checks.append(Check("sdk_wheel", SKIP, "vendor=True: the project uses the vendored SDK copy"))
    elif not p.wheel_path():
        checks.append(Check("sdk_wheel", ACTION, "sdk_volume_path / sdk_version are empty"))
    else:
        wheel = p.wheel_path()
        folder, name = wheel.rsplit("/", 1)
        try:
            names = {_text(getattr(e, "name", "")) or _text(getattr(e, "path", "")).rsplit("/", 1)[-1]
                     for e in ws.files.list_directory_contents(folder)}
            if name in names:
                checks.append(Check("sdk_wheel", PASS, f"{wheel} readable"))
            else:
                detail = f"{name} not in {folder}: deploy the SDK bundle for {p.sdk_version}"
                checks.append(Check("sdk_wheel", ACTION, detail))
        except Exception as e:  # noqa: BLE001
            checks.append(Check("sdk_wheel", ACTION, f"{folder} not readable ({_err(e)}); needs READ VOLUME"))
    return checks


def project_overrides(inputs: ProjectInputs | dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Both project bundles' overrides values from the same inputs (bundle dir -> values)."""
    p = _as_project_inputs(inputs)
    mv: dict[str, Any] = {
        "catalog": p.catalog,
        "schema_name": p.schema_name,
        "warehouse_id": p.warehouse_id,
        "consumer_group": p.consumer_group,
    }
    if p.source_catalog:
        mv["source_catalog"] = p.source_catalog
    if p.source_schema:
        mv["source_schema"] = p.source_schema
    if p.sdk_volume_path:
        mv["sdk_volume_path"] = p.sdk_volume_path
    if p.sdk_version:
        mv["sdk_version"] = p.sdk_version
    agents = {
        "catalog": p.catalog,
        "schema": p.resolved_schema(),
        "warehouse_id": p.warehouse_id,
        "consumer_group": p.consumer_group,
        "curator_group": p.curator_group,
    }
    return {MV_BUNDLE: mv, AGENTS_BUNDLE: agents}


def write_overrides(
    project_dir: str | Path, inputs: ProjectInputs | dict[str, Any], force: bool = False
) -> list[WriteResult]:
    """Write both gitignored ``variable-overrides.json`` files (metric views, agents).

    Same ``catalog`` in both; the agents ``schema`` is the metric-view
    ``schema_name`` resolved for the target (dev prefix). Edited files are kept
    unless ``force`` (``action == "skipped"``). Raises ``ValueError`` when a
    required input is empty.
    """
    p = _as_project_inputs(inputs)
    missing = [m for m in missing_project_inputs(p) if m != "project_dir"]
    if missing:
        raise ValueError("missing project inputs: " + ", ".join(missing))
    root = Path(project_dir)
    out = []
    for bundle, values in project_overrides(p).items():
        out.append(write_json(overrides_path(root / bundle, p.bundle_target), values, force=force))
    return out


def vars_file_values(inputs: ProjectInputs | dict[str, Any]) -> dict[str, str]:
    """genie-build-waves instance variables for this project."""
    p = _as_project_inputs(inputs)
    root = p.project_dir.rstrip("/")
    name = p.project_name or Path(root).name
    suffix = p.instance_suffix or "-" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return {
        "project_name": name,
        "instance_suffix": suffix,
        "build_root": root,
        "build_branch": p.branch,
        "manifest_path": f"{root}/docs/plans/waves.json",
        "skills_catalog": p.skills_catalog,
        "skills_schema": p.skills_schema,
    }


def write_vars_file(path: str | Path, inputs: ProjectInputs | dict[str, Any], force: bool = False) -> WriteResult:
    """Write the genie-build-waves vars file. Refuses a path inside the project (it holds workspace paths)."""
    p = _as_project_inputs(inputs)
    target = Path(path)
    project = Path(p.project_dir)
    if project.as_posix() and (target == project or project in target.parents):
        raise ValueError(f"vars file '{target}' must be outside the project '{project}'")
    return write_json(target, vars_file_values(p), force=force)


def project_commands(inputs: ProjectInputs | dict[str, Any]) -> list[str]:
    """Exact deploy, setup and run steps after scaffolding."""
    p = _as_project_inputs(inputs)
    root, t = p.project_dir.rstrip("/"), p.bundle_target
    gbw = p.genie_build_waves_dir.rstrip("/") or "<genie-build-waves>"
    vars_file = p.vars_file or "<vars file>"
    render = "gos-render-agents"  # console script of the installed SDK (geniespace:main)
    return [
        f"cd {root}/{MV_BUNDLE} && databricks bundle validate --strict --target {t}",
        f"cd {root}/{AGENTS_BUNDLE} && {render} render agents .rendered "
        f"--params .databricks/bundle/{t}/{OVERRIDES_FILE} && databricks bundle validate --strict --target {t}",
        f"Commit the scaffolded files on branch {p.branch or '<feature branch>'} (never main) and push",
        f"cd {gbw} && python scripts/deploy_instance.py --target dev --vars {vars_file} --check-only",
        f"cd {gbw} && python scripts/deploy_instance.py --target dev --vars {vars_file}",
        f"Run setup: {gbw}/scripts/setup_helper with vars_file={vars_file}, action=run_setup "
        "(expect 0 manifest errors)",
        "Start the build job from the setup output (job parameters branch, build_root, manifest_path) "
        "and watch each wave gate",
    ]


def checklist(state: dict[str, Any]) -> str:
    """Markdown checklist of what is done and what the owner still has to do.

    ``state`` keys (all optional): ``checks`` (list of ``Check``), ``scaffold``
    (``ScaffoldReport`` or dict), ``overrides`` (list of ``WriteResult``),
    ``vars_file`` (``WriteResult``), ``commands`` (list of str), ``missing``
    (list of input names).
    """
    lines = ["## Setup checklist", ""]

    def box(done: bool, text: str) -> None:
        lines.append(f"- [{'x' if done else ' '}] {text}")

    missing = state.get("missing") or []
    box(not missing, "Required inputs set" + (f" (missing: {', '.join(missing)})" if missing else ""))
    for c in state.get("checks") or []:
        box(c.status != ACTION, f"{c.name}: {c.status} - {c.detail}")
    sc = state.get("scaffold")
    if sc is None:
        box(False, "Project scaffolded (set target_dir)")
    else:
        d = sc if isinstance(sc, dict) else sc.to_dict()
        skipped = d.get("skipped") or []
        kept = f", {len(skipped)} kept (differ; force to replace)" if skipped else ""
        box(not skipped, f"Project scaffolded in {d.get('target_dir')}: {d.get('files_written', 0)} written, "
            f"{len(d.get('unchanged') or [])} unchanged{kept}")
    ov = state.get("overrides")
    if not ov:
        box(False, "Both variable-overrides.json files written")
    for r in ov or []:
        note = " (edited; force to replace)" if r.action == "skipped" else ""
        box(r.action != "skipped", f"{r.path}: {r.action}{note}")
    vf = state.get("vars_file")
    if vf is None:
        box(False, "genie-build-waves vars file written (set vars_file)")
    else:
        box(vf.action != "skipped", f"Vars file {vf.path}: {vf.action}")
    cmds = state.get("commands") or []
    if cmds:
        lines += ["", "Owner steps, in order:", ""]
        lines += [f"{i}. `{c}`" if c.startswith("cd ") else f"{i}. {c}" for i, c in enumerate(cmds, 1)]
    return "\n".join(lines) + "\n"
