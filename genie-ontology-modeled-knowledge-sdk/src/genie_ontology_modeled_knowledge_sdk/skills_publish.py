"""Publish the SDK skills to the Unity Gateway skills library (build-1 R1).

Public API:

* ``load_mapping(path, catalog, schema) -> list[SkillTarget]`` - read ``ci/skills.yaml`` and
  substitute ``${SKILLS_CATALOG}`` / ``${SKILLS_SCHEMA}``
* ``read_skill_files(folder) -> dict[str, str]`` - every file of a skill folder (UTF-8 text)
* ``skill_limit_errors(folder) -> list[str]`` - platform limits + ``SKILL.md`` front matter
* ``check_schema(ws, catalog, schema, create_schema=False) -> dict`` - report; never creates
  unless ``create_schema=True``
* ``published_files(ws, target) -> dict[str, str] | None`` - files of the published skill
  (``None`` when it does not exist)
* ``plan_publish(skills_dir, mapping, ws=None) -> dict[str, SkillPlan]`` - diff of local files
  vs. the published version (everything is ``add`` when ``ws`` is ``None``)
* ``publish(ws, skills_dir, mapping, dry_run=False) -> dict[str, list[str]]`` - idempotent
  create -> upload (changed files only) -> finalize; returns the changed files per skill id.
  A second run with no local changes uploads nothing, finalizes nothing and returns empty lists.

The flow is the same one genie-build-waves setup uses: ``ai_gateway.create_skill`` (parent
``schemas/<catalog>.<schema>``), ``files.upload`` under ``/Skills/<catalog>/<schema>/<id>/``,
then ``ai_gateway.finalize_skill`` (name ``skills/<catalog>.<schema>.<id>``). No grants are
applied here; see ``docs/skills/README.md``. Files that exist only in the published version are
reported as ``stale`` and left in place.

Pure Python: the ``WorkspaceClient`` is injected, so tests pass a fake.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

__all__ = [
    "MAX_ENTRIES",
    "MAX_FOLDER_LEVELS",
    "SkillTarget",
    "SkillPlan",
    "load_mapping",
    "read_skill_files",
    "front_matter",
    "skill_limit_errors",
    "check_schema",
    "published_files",
    "plan_publish",
    "publish",
    "list_published",
]

# Unity Gateway skill limits: text files only, at most three folder levels, at most 50 files or folders.
MAX_FOLDER_LEVELS = 3
MAX_ENTRIES = 50
_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_VAR_RE = re.compile(r"\$\{(SKILLS_CATALOG|SKILLS_SCHEMA)\}")
_SKIP = {"__pycache__", ".ipynb_checkpoints", ".DS_Store"}


@dataclass(frozen=True)
class SkillTarget:
    """One mapping entry: a skill folder and its Unity Catalog id."""

    folder: str  # folder name under skills_dir, e.g. ontology-deep-eda
    catalog: str
    schema: str
    skill_id: str  # snake_case, e.g. ontology_deep_eda

    @property
    def fqn(self) -> str:
        return f"{self.catalog}.{self.schema}.{self.skill_id}"

    @property
    def name(self) -> str:
        """Resource name for get/finalize (``skills/`` prefix)."""
        return f"skills/{self.fqn}"

    @property
    def parent(self) -> str:
        return f"schemas/{self.catalog}.{self.schema}"

    @property
    def files_root(self) -> str:
        return f"/Skills/{self.catalog}/{self.schema}/{self.skill_id}"


@dataclass
class SkillPlan:
    """Diff of one skill folder against its published version."""

    target: SkillTarget
    exists: bool = False
    add: list[str] = field(default_factory=list)
    update: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    stale: list[str] = field(default_factory=list)

    @property
    def changed(self) -> list[str]:
        return sorted(self.add + self.update)

    def to_dict(self) -> dict[str, Any]:
        return {
            "fqn": self.target.fqn,
            "folder": self.target.folder,
            "exists": self.exists,
            "add": self.add,
            "update": self.update,
            "unchanged": self.unchanged,
            "stale": self.stale,
        }


def _is_not_found(e: Exception) -> bool:
    return type(e).__name__ in {"NotFound", "FakeNotFound", "ResourceDoesNotExist"}


def load_mapping(path: str | Path, catalog: str, schema: str) -> list[SkillTarget]:
    """Read the skills mapping and substitute the catalog and schema placeholders."""
    if not catalog or not schema:
        raise ValueError("skills catalog and schema are required")
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    values = {"SKILLS_CATALOG": catalog, "SKILLS_SCHEMA": schema}
    out: list[SkillTarget] = []
    seen: set[str] = set()
    for i, entry in enumerate(data.get("skills") or []):
        source = str(entry.get("source", "")).rstrip("/")
        target = _VAR_RE.sub(lambda m: values[m.group(1)], str(entry.get("target", "")))
        parts = target.split(".")
        if not source or len(parts) != 3 or not all(parts):
            raise ValueError(f"skills[{i}]: need source and a 3-part target, got {entry!r}")
        if not _ID_RE.match(parts[2]):
            raise ValueError(f"skills[{i}]: skill id '{parts[2]}' is not snake_case")
        if parts[2] in seen:
            raise ValueError(f"skills[{i}]: duplicate skill id '{parts[2]}'")
        seen.add(parts[2])
        out.append(SkillTarget(folder=source.rsplit("/", 1)[-1], catalog=parts[0], schema=parts[1], skill_id=parts[2]))
    if not out:
        raise ValueError(f"{path}: no skills listed")
    return out


def _walk(folder: Path) -> tuple[list[Path], list[Path]]:
    files: list[Path] = []
    dirs: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if d not in _SKIP)
        base = Path(dirpath)
        dirs += [base / d for d in dirnames]
        files += [base / f for f in sorted(filenames) if f not in _SKIP]
    return files, dirs


def read_skill_files(folder: str | Path) -> dict[str, str]:
    """Return ``{relative posix path: text}`` for every file of a skill folder."""
    root = Path(folder)
    files, _ = _walk(root)
    return {f.relative_to(root).as_posix(): f.read_text(encoding="utf-8") for f in files}


def front_matter(text: str) -> dict[str, Any]:
    """Parse the YAML front matter of a ``SKILL.md`` (empty dict when absent)."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*(\n|$)", text, re.S)
    if not m:
        return {}
    data = yaml.safe_load(m.group(1))
    return data if isinstance(data, dict) else {}


def skill_limit_errors(folder: str | Path) -> list[str]:
    """Platform-limit and front matter problems for one skill folder (empty = valid)."""
    root = Path(folder)
    if not (root / "SKILL.md").is_file():
        return [f"{root.name}: SKILL.md missing"]
    errors: list[str] = []
    files, dirs = _walk(root)
    if len(files) + len(dirs) > MAX_ENTRIES:
        errors.append(f"{root.name}: {len(files) + len(dirs)} files or folders (max {MAX_ENTRIES})")
    for d in dirs:
        depth = len(d.relative_to(root).parts)
        if depth > MAX_FOLDER_LEVELS:
            errors.append(f"{root.name}: folder {d.relative_to(root).as_posix()} is {depth} levels deep (max {MAX_FOLDER_LEVELS})")
    for f in files:
        try:
            f.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            errors.append(f"{root.name}: {f.relative_to(root).as_posix()} is not a UTF-8 text file")
    fm = front_matter((root / "SKILL.md").read_text(encoding="utf-8", errors="replace"))
    for key in ("name", "description"):
        if not str(fm.get(key) or "").strip():
            errors.append(f"{root.name}: SKILL.md front matter has no '{key}'")
    if fm.get("name") and fm.get("name") != root.name:
        errors.append(f"{root.name}: front matter name '{fm.get('name')}' differs from the folder name")
    return errors


def check_schema(ws: Any, catalog: str, schema: str, create_schema: bool = False) -> dict[str, Any]:
    """Report whether the skills schema exists; create it only when ``create_schema`` is true."""
    full = f"{catalog}.{schema}"
    try:
        ws.schemas.get(full)
        return {"schema": full, "exists": True, "created": False, "error": ""}
    except Exception as e:  # noqa: BLE001 - reported, never raised
        if not _is_not_found(e):
            return {"schema": full, "exists": False, "created": False, "error": f"{type(e).__name__}: {e}"}
    if not create_schema:
        return {"schema": full, "exists": False, "created": False, "error": "schema does not exist (create_schema=False)"}
    ws.schemas.create(name=schema, catalog_name=catalog)
    return {"schema": full, "exists": True, "created": True, "error": ""}


def _skill_exists(ws: Any, target: SkillTarget) -> bool:
    try:
        ws.ai_gateway.get_skill(name=target.name)
        return True
    except Exception as e:
        if _is_not_found(e):
            return False
        raise


def _list_files(ws: Any, directory: str) -> list[str]:
    out: list[str] = []
    for entry in ws.files.list_directory_contents(directory):
        if entry.is_directory:
            out += _list_files(ws, entry.path.rstrip("/"))
        else:
            out.append(entry.path)
    return out


def published_files(ws: Any, target: SkillTarget) -> dict[str, str] | None:
    """Files of the published skill as ``{relative path: text}``; ``None`` if the skill is missing."""
    if not _skill_exists(ws, target):
        return None
    try:
        paths = _list_files(ws, target.files_root)
    except Exception as e:
        if _is_not_found(e):
            return {}
        raise
    out: dict[str, str] = {}
    for p in paths:
        body = ws.files.download(p).contents.read()
        out[p[len(target.files_root) + 1 :]] = body.decode("utf-8") if isinstance(body, bytes) else str(body)
    return out


def plan_publish(skills_dir: str | Path, mapping: list[SkillTarget], ws: Any = None) -> dict[str, SkillPlan]:
    """Diff every mapped skill folder against its published version (keyed by skill id)."""
    plans: dict[str, SkillPlan] = {}
    for t in mapping:
        folder = Path(skills_dir) / t.folder
        if not folder.is_dir():
            raise FileNotFoundError(f"skill folder missing: {folder}")
        local = read_skill_files(folder)
        remote = published_files(ws, t) if ws is not None else None
        plan = SkillPlan(target=t, exists=remote is not None)
        remote = remote or {}
        for rel in sorted(local):
            if rel not in remote:
                plan.add.append(rel)
            elif remote[rel] != local[rel]:
                plan.update.append(rel)
            else:
                plan.unchanged.append(rel)
        plan.stale = sorted(set(remote) - set(local))
        plans[t.skill_id] = plan
    return plans


def _skill_obj(comment: str) -> Any:
    try:
        from databricks.sdk.service.catalog import Skill  # must be the dataclass, not a dict
    except ImportError:  # pragma: no cover - very old SDKs have no skills API
        return {"comment": comment}
    return Skill(comment=comment)


def publish(
    ws: Any,
    skills_dir: str | Path,
    mapping: list[SkillTarget],
    *,
    dry_run: bool = False,
    comment: str = "Genie Ontology Modeled Knowledge SDK skill",
) -> dict[str, list[str]]:
    """Create missing skills, upload changed files and finalize; returns changed files per skill id.

    Idempotent: a skill whose files all match the published version is not uploaded or finalized.
    ``dry_run`` returns what would change without writing anything.
    """
    plans = plan_publish(skills_dir, mapping, ws)
    changed: dict[str, list[str]] = {}
    for skill_id, plan in plans.items():
        t = plan.target
        files = plan.changed
        changed[skill_id] = files
        if dry_run or (plan.exists and not files):
            continue
        if not plan.exists:
            try:
                ws.ai_gateway.create_skill(parent=t.parent, skill_id=t.skill_id, skill=_skill_obj(comment))
            except Exception as e:
                if type(e).__name__ != "AlreadyExists":
                    raise
        local = read_skill_files(Path(skills_dir) / t.folder)
        for rel in files:
            ws.files.upload(f"{t.files_root}/{rel}", io.BytesIO(local[rel].encode("utf-8")), overwrite=True)
        ws.ai_gateway.finalize_skill(name=t.name)
    return changed


def list_published(ws: Any, catalog: str, schema: str) -> list[str]:
    """Skill ids (fully qualified) published in ``catalog.schema``."""
    names = [str(s.name) for s in ws.ai_gateway.list_skills(parent=f"schemas/{catalog}.{schema}")]
    return sorted(n.removeprefix("skills/") for n in names)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Publish the SDK skills to Unity Catalog (idempotent).")
    p.add_argument("--mapping", required=True, help="ci/skills.yaml")
    p.add_argument("--skills-dir", required=True, help="SDK skills/ folder")
    p.add_argument("--catalog", required=True)
    p.add_argument("--schema", required=True)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--check-only", action="store_true", help="only run the limit checks (no workspace calls)")
    a = p.parse_args(argv)
    mapping = load_mapping(a.mapping, a.catalog, a.schema)
    errors = [e for t in mapping for e in skill_limit_errors(Path(a.skills_dir) / t.folder)]
    if errors or a.check_only:
        print(json.dumps({"errors": errors}, indent=2))
        return 1 if errors else 0
    from databricks.sdk import WorkspaceClient

    ws = WorkspaceClient()
    report = check_schema(ws, a.catalog, a.schema)
    if not report["exists"]:
        print(json.dumps(report, indent=2))
        return 1
    print(json.dumps(publish(ws, a.skills_dir, mapping, dry_run=a.dry_run), indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
