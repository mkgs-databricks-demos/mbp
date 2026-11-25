"""Scaffold a Genie Ontology run project from the SDK templates.

Public API (cross-session contract, see ``docs/plans/INDEX.md``):

* ``scaffold_project(cfg, target_dir, sdk_root, *, force=False, vendor=False) -> ScaffoldReport``
* ``vendored_modules(sdk_root) -> tuple[str, ...]`` - import closure vendored with ``vendor=True``
* ``ScaffoldReport`` - what was written, left unchanged, skipped or overwritten
* CLI: ``python -m genie_ontology_modeled_knowledge_sdk.scaffold --config sdk_config.json --target <dir>``

What it creates (``docs/plans/INDEX.md`` "Run project layout")::

    <project>/
    ├── sdk_config.json
    ├── PROJECT_MEMORY.md                 # templates/run/PROJECT_MEMORY.md
    ├── ontology-metric-views/            # templates/ontology-metric-views
    │   └── src/genie_ontology_modeled_knowledge_sdk_vendored/   # only with vendor=True
    ├── ontology-genie-agents/            # templates/ontology-genie-agents
    └── docs/
        ├── plans/                        # templates/run/{waves.json,INDEX.md,README.md,plans/}
        └── research/ semantics/ context/ data_profiles/ registration/
            pages/ deployment/ tuning/ sessions/   (each with .gitkeep)

Rules:

* Only the run-kit tokens ``{{project_name}}``, ``{{domain_name}}`` and
  ``{{bundle_target}}`` are rendered. Every other ``{{...}}`` (Jobs dynamic value
  references such as ``{{input.name}}``) and every ``${...}`` stay as they are.
* ``ontology-metric-views/databricks.yml``: the ``schema_name`` variable default
  is set to ``sdk_config.target_schema`` (the template's generic ``ontology``
  default is not kept), so DAB 1 and the resolved target agree from the start.
* The template's placeholder agent ``agents/ontology_agent.geniespace.json`` is
  not copied (agent curation writes the real agents); ``agents/.gitkeep`` keeps
  the folder.
* Existing files are never overwritten unless ``force=True``. A file whose
  content already matches is left alone (so a second run writes 0 files).
* ``.databricks/`` (bundle state, ``variable-overrides.json``) and ``.rendered/``
  (rendered agent files) are never read from the templates nor written in the
  project, even with ``force``.
* Wheel first: by default (``vendor=False``) nothing is vendored and the
  template notebooks import the installed SDK wheel (the job environment
  installs it). The template's ``src/genie_ontology_modeled_knowledge_sdk_vendored/``
  folder is not copied.
* ``vendor=True`` (opt-in, for workspaces without package egress) copies the
  import closure of every SDK module the template notebooks import, byte for
  byte from ``src/genie_ontology_modeled_knowledge_sdk/``, plus the folder's
  README and a ``VENDORED_VERSION`` file with the SDK version.

Pure Python: no Spark, no Databricks API calls.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from genie_ontology_modeled_knowledge_sdk.config import SdkConfig, config_from_dict, load_config

__all__ = [
    "PLACEHOLDER_FILES",
    "RUN_TOKENS",
    "VENDORED_DIR",
    "VENDORED_VERSION_FILE",
    "DOCS_DIRS",
    "vendored_modules",
    "ScaffoldReport",
    "render_schema_name",
    "render_tokens",
    "scaffold_project",
    "main",
]

RUN_TOKENS = ("project_name", "domain_name", "bundle_target")
_TOKEN_RE = re.compile(r"\{\{\s*(" + "|".join(RUN_TOKENS) + r")\s*\}\}")

VENDORED_DIR = Path("ontology-metric-views/src/genie_ontology_modeled_knowledge_sdk_vendored")
VENDORED_VERSION_FILE = "VENDORED_VERSION"
_PKG = "genie_ontology_modeled_knowledge_sdk"
# `genie_ontology_modeled_knowledge_sdk.<mod>` in imports, and `from genie_ontology_modeled_knowledge_sdk import a, b`.
_SDK_DOTTED_RE = re.compile(r"\b" + _PKG + r"\.([A-Za-z_][A-Za-z0-9_]*)")
_SDK_FROM_RE = re.compile(r"(?m)^\s*from\s+" + _PKG + r"\s+import\s+\(?([A-Za-z0-9_,\s]+)\)?")

DOCS_DIRS = (
    "research",
    "semantics",
    "context",
    "data_profiles",
    "registration",
    "pages",
    "deployment",
    "tuning",
    "sessions",
)

# Never copied from the templates and never written in the project.
PROTECTED_DIRS = frozenset({".databricks", ".rendered"})
_SKIP_DIRS = PROTECTED_DIRS | {"__pycache__", ".pytest_cache", ".ipynb_checkpoints"}
_SKIP_SUFFIXES = (".pyc",)

# (template sub-folder, project destination); run kit handled separately.
_BUNDLES = (
    ("ontology-metric-views", "ontology-metric-views"),
    ("ontology-genie-agents", "ontology-genie-agents"),
)
_RUN_TO_PLANS = ("waves.json", "INDEX.md", "README.md", "plans")

# Template placeholders that are not copied into a project (project-relative paths).
PLACEHOLDER_FILES = frozenset({Path("ontology-genie-agents/agents/ontology_agent.geniespace.json")})
_AGENTS_KEEP = Path("ontology-genie-agents/agents/.gitkeep")

_MV_BUNDLE_YML = Path("ontology-metric-views/databricks.yml")
# The `default:` line inside the `schema_name:` variable block of DAB 1.
_SCHEMA_DEFAULT_RE = re.compile(r"(?m)^(  schema_name:[ \t]*\n(?:    [^\n]*\n)*?    default:[ \t]*)[^\n]*$")
_PLAIN_SCALAR_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass
class ScaffoldReport:
    """Outcome of ``scaffold_project``. Paths are POSIX, relative to ``target_dir``."""

    target_dir: str
    written: list[str] = field(default_factory=list)  # created (did not exist)
    overwritten: list[str] = field(default_factory=list)  # differed, replaced because force=True
    unchanged: list[str] = field(default_factory=list)  # existed with identical content
    skipped: list[str] = field(default_factory=list)  # existed with different content, kept

    @property
    def files_written(self) -> int:
        """Number of files actually written (created + overwritten)."""
        return len(self.written) + len(self.overwritten)

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_dir": self.target_dir,
            "files_written": self.files_written,
            "written": list(self.written),
            "overwritten": list(self.overwritten),
            "unchanged": list(self.unchanged),
            "skipped": list(self.skipped),
        }


def render_tokens(text: str, values: dict[str, str]) -> str:
    """Replace the run-kit ``{{token}}`` placeholders; leave everything else alone."""
    return _TOKEN_RE.sub(lambda m: values.get(m.group(1), m.group(0)), text)


def render_schema_name(text: str, schema_name: str) -> str:
    """Set the ``schema_name`` variable default in the metric-views ``databricks.yml``.

    ``ValueError`` if the variable block or its ``default:`` line is not found.
    """
    value = schema_name if _PLAIN_SCALAR_RE.match(schema_name) else json.dumps(schema_name)
    new, n = _SCHEMA_DEFAULT_RE.subn(lambda m: m.group(1) + value, text, count=1)
    if n != 1:
        raise ValueError(f"{_MV_BUNDLE_YML.as_posix()}: no 'schema_name' variable with a 'default:' line")
    return new


def _sdk_module_refs(text: str, pkg: Path) -> set[str]:
    """SDK module file names (``x.py``) referenced in ``text`` that exist in ``pkg``."""
    names = set(_SDK_DOTTED_RE.findall(text))
    for group in _SDK_FROM_RE.findall(text):
        names.update(n.strip() for n in group.split(",") if n.strip())
    return {f"{n}.py" for n in names if (pkg / f"{n}.py").is_file()}


def _notebook_code(path: Path) -> str:
    nb = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") == "code":
            src = cell.get("source", "")
            out.append(src if isinstance(src, str) else "".join(src))
    return "\n".join(out)


def _package_dir(sdk_root: Path) -> Path:
    """SDK package folder to vendor from: ``<sdk_root>/src/<pkg>`` in an SDK checkout,
    else the installed package (wheel install, where ``sdk_root`` only provides templates)."""
    src_pkg = sdk_root / "src" / _PKG
    if src_pkg.is_dir():
        return src_pkg
    return Path(__file__).resolve().parent


def vendored_modules(sdk_root: str | Path) -> tuple[str, ...]:
    """Import closure of the SDK modules the metric-views template notebooks import.

    Parses the template notebooks' code cells for ``genie_ontology_modeled_knowledge_sdk.*``
    imports, then follows each module's own SDK imports. Sorted file names. Module
    files come from ``<sdk_root>/src`` when present, else from the installed package.
    """
    sdk = Path(sdk_root)
    pkg = _package_dir(sdk)
    todo: set[str] = set()
    for nb in sorted((sdk / "templates" / "ontology-metric-views" / "notebooks").glob("*.ipynb")):
        todo |= _sdk_module_refs(_notebook_code(nb), pkg)
    seen: set[str] = set()
    while todo:
        mod = todo.pop()
        if mod in seen:
            continue
        seen.add(mod)
        todo |= _sdk_module_refs((pkg / mod).read_text(encoding="utf-8"), pkg) - seen
    return tuple(sorted(seen))


def _sdk_version(sdk_root: Path) -> str:
    """``[project] version`` from the SDK's pyproject.toml, else the installed ``__version__``."""
    pyproject = sdk_root / "pyproject.toml"
    if pyproject.is_file():
        m = re.search(r'(?m)^version\s*=\s*"([^"]+)"', pyproject.read_text(encoding="utf-8"))
        if m:
            return m.group(1)
    from genie_ontology_modeled_knowledge_sdk import __version__

    return __version__


def _render_bytes(data: bytes, values: dict[str, str]) -> bytes:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return data  # binary: copy as is
    return render_tokens(text, values).encode("utf-8")


def _iter_files(root: Path) -> Iterator[Path]:
    """Yield template files under ``root`` (sorted), skipping protected/cache dirs."""
    for p in sorted(root.rglob("*")):
        rel_parts = p.relative_to(root).parts
        if any(part in _SKIP_DIRS for part in rel_parts):
            continue
        if p.is_file() and not p.name.endswith(_SKIP_SUFFIXES):
            yield p


def _is_protected(rel: Path) -> bool:
    return any(part in PROTECTED_DIRS for part in rel.parts)


def _plan(sdk_root: Path, cfg: SdkConfig, values: dict[str, str], vendor: bool = False) -> list[tuple[Path, bytes]]:
    """Return ``(relative destination, content)`` for every file to scaffold."""
    templates = sdk_root / "templates"
    pkg = _package_dir(sdk_root)
    missing = [str(p) for p in (templates / "run",) if not p.is_dir()]
    missing += [str(templates / s) for s, _ in _BUNDLES if not (templates / s).is_dir()]
    if missing:
        raise FileNotFoundError(f"sdk_root '{sdk_root}' is missing: {', '.join(missing)}")

    out: list[tuple[Path, bytes]] = []

    for src_name, dst_name in _BUNDLES:
        src = templates / src_name
        for f in _iter_files(src):
            rel = Path(dst_name) / f.relative_to(src)
            if rel in PLACEHOLDER_FILES:
                continue
            if not vendor and VENDORED_DIR in rel.parents:
                continue  # wheel-first: no vendored folder at all
            content = _render_bytes(f.read_bytes(), values)
            if rel == _MV_BUNDLE_YML:
                content = render_schema_name(content.decode("utf-8"), cfg.target_schema).encode("utf-8")
            out.append((rel, content))
    if not any(rel == _AGENTS_KEEP for rel, _ in out):
        out.append((_AGENTS_KEEP, b""))

    run = templates / "run"
    for name in _RUN_TO_PLANS:
        p = run / name
        if p.is_dir():
            for f in _iter_files(p):
                out.append((Path("docs/plans") / f.relative_to(run), _render_bytes(f.read_bytes(), values)))
        elif p.is_file():
            out.append((Path("docs/plans") / name, _render_bytes(p.read_bytes(), values)))
        else:
            raise FileNotFoundError(f"run kit file missing: {p}")
    memory = run / "PROJECT_MEMORY.md"
    if not memory.is_file():
        raise FileNotFoundError(f"run kit file missing: {memory}")
    out.append((Path("PROJECT_MEMORY.md"), _render_bytes(memory.read_bytes(), values)))

    if vendor:
        for module in vendored_modules(sdk_root):
            out.append((VENDORED_DIR / module, (pkg / module).read_bytes()))  # verbatim, not rendered
        out.append((VENDORED_DIR / VENDORED_VERSION_FILE, (_sdk_version(sdk_root) + "\n").encode("utf-8")))

    config_text = json.dumps(cfg.to_dict(), indent=2) + "\n"
    out.append((Path("sdk_config.json"), config_text.encode("utf-8")))

    for d in DOCS_DIRS:
        out.append((Path("docs") / d / ".gitkeep", b""))

    # Later entries never silently replace earlier ones.
    seen: set[Path] = set()
    for rel, _ in out:
        if rel in seen:
            raise ValueError(f"scaffold: two sources map to '{rel.as_posix()}'")
        seen.add(rel)
    return out


def scaffold_project(
    cfg: SdkConfig | dict[str, Any],
    target_dir: str | Path,
    sdk_root: str | Path,
    *,
    force: bool = False,
    project_name: str | None = None,
    bundle_target: str = "dev",
    vendor: bool = False,
) -> ScaffoldReport:
    """Create (or complete) a run project in ``target_dir`` from ``sdk_root``.

    ``cfg`` is validated first (``ValueError`` if invalid). ``project_name``
    defaults to the name of ``target_dir``; ``bundle_target`` to ``dev``.
    Existing files are kept unless ``force``; ``.databricks/`` and ``.rendered/``
    are never touched. ``vendor=True`` copies the SDK modules the notebooks
    import (opt-in; the default installs the SDK wheel instead).
    """
    c = cfg if isinstance(cfg, SdkConfig) else config_from_dict(cfg)
    target = Path(target_dir)
    sdk = Path(sdk_root)
    values = {
        "project_name": project_name or target.resolve().name,
        "domain_name": c.domain_name,
        "bundle_target": bundle_target,
    }
    report = ScaffoldReport(target_dir=str(target))

    for rel, content in _plan(sdk, c, values, vendor=vendor):
        if _is_protected(rel):  # defensive: the plan never yields these
            continue
        dst = target / rel
        key = rel.as_posix()
        if dst.exists():
            if dst.is_file() and dst.read_bytes() == content:
                report.unchanged.append(key)
                continue
            if not force or not dst.is_file():
                report.skipped.append(key)
                continue
            dst.write_bytes(content)
            report.overwritten.append(key)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(content)
        report.written.append(key)
    return report


def _default_sdk_root() -> Path:
    # src/genie_ontology_modeled_knowledge_sdk/scaffold.py -> SDK root is two levels above the package.
    # Installed from the wheel, there is no checkout: pass --sdk-root (templates live there).
    return Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m genie_ontology_modeled_knowledge_sdk.scaffold",
        description="Scaffold a Genie Ontology run project from the SDK templates.",
    )
    parser.add_argument("--config", required=True, help="sdk_config.json (or .yml)")
    parser.add_argument("--target", required=True, help="project folder to create or complete")
    parser.add_argument("--sdk-root", default=None, help="SDK root (default: this package's repo)")
    parser.add_argument("--project-name", default=None)
    parser.add_argument("--bundle-target", default="dev")
    parser.add_argument("--force", action="store_true", help="overwrite files that differ")
    parser.add_argument(
        "--vendor",
        action="store_true",
        help="copy the SDK modules the notebooks import into the project (opt-in; default installs the wheel)",
    )
    args = parser.parse_args(argv)
    try:
        cfg = load_config(args.config)
        report = scaffold_project(
            cfg,
            args.target,
            args.sdk_root or _default_sdk_root(),
            force=args.force,
            project_name=args.project_name,
            bundle_target=args.bundle_target,
            vendor=args.vendor,
        )
    except (ValueError, FileNotFoundError) as e:
        print(f"scaffold: {e}", file=sys.stderr)
        return 1
    print(json.dumps(report.to_dict(), indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
