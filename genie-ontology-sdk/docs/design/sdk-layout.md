# Genie Ontology SDK — Repository Layout

The layout of the SDK repository (`build_root`) and which build-0 session owns each part. Module APIs are the cross-session contracts in [docs/plans/INDEX.md](../plans/INDEX.md#cross-session-contracts); this page is the map.

## Tree

```
genie-ontology-sdk/
├── pyproject.toml                      # 01  package metadata, deps, pytest config
├── src/
│   └── genie_ontology_sdk/
│       ├── __init__.py                 # 01  __version__, module list
│       ├── config.py                   # 01  input contract (SdkConfig, validate, check_access, expand_tables)
│       ├── schemas/
│       │   └── sdk_config.schema.json  # 01  JSON Schema (draft 2020-12) for sdk_config.json
│       ├── mv_yaml.py                  # 02  metric view YAML: load, substitute, validate MV001-MV007, render DDL, CLI
│       ├── manifest.py                 # 02  manifest.json (forEach registration input)
│       ├── geniespace.py               # 03  agent planning (<=50 MVs per agent), .geniespace.json builder, CLI
│       ├── pages.py                    # 04  glossary terms -> UC Pages payloads, upsert
│       ├── benchmark.py                # 04  benchmark questions, run, score, results markdown
│       └── scaffold.py                 # 09  scaffold_project for a run project
├── tests/
│   ├── conftest.py                     # 01  FakeWorkspaceClient, tpch_config fixture
│   ├── test_config.py                  # 01
│   ├── test_mv_yaml.py, test_manifest.py            # 02  (+ fixtures/metric_views/)
│   ├── test_geniespace.py                           # 03  (+ fixtures/geniespace/)
│   ├── test_pages.py, test_benchmark.py             # 04  (+ fixtures/glossary/, fixtures/benchmark/)
│   ├── test_template_mv_bundle.py                   # 06
│   ├── test_template_agent_bundle.py                # 07
│   └── test_run_kit.py                              # 08
├── skills/                             # Genie Code skills, one folder per pipeline stage
│   ├── ontology-domain-research/       # 05a
│   ├── ontology-context-extraction/    # 05a
│   ├── ontology-deep-eda/              # 05a
│   ├── ontology-mv-synthesis/          # 05b
│   ├── ontology-agent-curation/        # 05b
│   └── ontology-tuning/                # 05b
├── templates/
│   ├── ontology-metric-views/          # 06  DAB 1: schema resource, forEach registration job, smoke + cardinality notebooks
│   ├── ontology-genie-agents/          # 07  DAB 2: genie_spaces resource (engine: direct)
│   └── run/                            # 08  pipeline-run kit: waves.json, INDEX, plans, PROJECT_MEMORY starter, README
├── notebooks/                          # 09  init notebook (calls config + scaffold)
├── examples/
│   └── tpch/                           # 09 scaffold, then dogfood sessions 10a-16 (see INDEX shared-files table)
└── docs/
    ├── design/                         # L100, L200-A..H, this page (01), l300-pipeline/ (reference)
    ├── plans/                          # build-0 manifest + plans (read-only during the build)
    ├── sessions/                       # session summaries (each session writes its own)
    └── research/, semantics/, diagrams/, pitch/
```

## Ownership by session

| Session | Wave | Owns |
|---|---|---|
| 01 | 0-0 | `pyproject.toml`, `src/genie_ontology_sdk/{__init__,config}.py`, `src/genie_ontology_sdk/schemas/**`, `tests/conftest.py`, `tests/test_config.py`, `docs/design/sdk-layout.md` |
| 02 | 0-1 | `mv_yaml.py`, `manifest.py`, their tests, `tests/fixtures/metric_views/**` |
| 03 | 0-1 | `geniespace.py`, its tests, `tests/fixtures/geniespace/**` |
| 04 | 0-1 | `pages.py`, `benchmark.py`, their tests, `tests/fixtures/{glossary,benchmark}/**` |
| 05a | 0-1 | `skills/ontology-{domain-research,context-extraction,deep-eda}/**` |
| 05b | 0-1 | `skills/ontology-{mv-synthesis,agent-curation,tuning}/**` |
| 06 | 0-2 | `templates/ontology-metric-views/**`, `tests/test_template_mv_bundle.py` |
| 07 | 0-2 | `templates/ontology-genie-agents/**`, `tests/test_template_agent_bundle.py` |
| 08 | 0-2 | `templates/run/**`, `tests/test_run_kit.py` |
| 09 | 0-3 | `scaffold.py`, `notebooks/`, `examples/tpch/` scaffold |
| 10a-16 | 0-4..0-9 | `examples/tpch/**` outputs, per the INDEX shared-files table |
| 17 | 0-10 | build-0 docs (`README.md`, `PROJECT_MEMORY.md`, L100 updates) |

The manifest (`docs/plans/waves.json`) is authoritative for `owned_paths`; this table summarizes it.

## Conventions

* **Pure Python 3.11+** in `src/`: no Spark imports. Databricks access goes through an injected `WorkspaceClient`; tests pass `tests/conftest.py::FakeWorkspaceClient`.
* **Shared test scaffolding:** `tests/conftest.py` is owned by 01. Other sessions add fixtures in their own test files (or `tests/fixtures/<area>/`) and request changes to `conftest.py` through their status file.
* **Package data:** JSON schemas live in `src/genie_ontology_sdk/schemas/` and are read with `importlib.resources`; `pyproject.toml` ships `schemas/*.json`.
* **Running tests:** pytest fails in place on `/Workspace` (OSError 95). Copy first: `cp -r <build_root> /tmp/gos && cd /tmp/gos && python -m pytest -q`. `pyproject.toml` sets `pythonpath = ["src"]` and `testpaths = ["tests"]`.
* **No workspace-specific values** (hosts, user names, real catalogs other than `samples`) in committed files outside `docs/sessions/`. `main` / `ontology_tpch` are documented placeholders.

## Input contract summary (`sdk_config.json`)

| Key | Required | Notes |
|---|---|---|
| `target_catalog`, `target_schema` | yes | where metric views are registered |
| `domain_name` | yes | snake_case (`^[a-z][a-z0-9_]*$`) |
| `domain_context` | yes | free text |
| `source_catalogs` / `source_schemas` / `source_tables` | at least one non-empty | schemas are `catalog.schema`, tables `catalog.schema.table` |
| `supplemental_volume_dirs`, `dashboard_inputs` | no | `/Volumes/...` paths |
| `source_catalog_for_reads`, `source_schema_for_reads` | no | override MV `source:` parameters |
| `warehouse_id` | no | SQL warehouse |
| `max_metric_views_per_agent` | no | integer >= 1, default 50 |
| `project_root`, `repo_path` | no | workspace paths of the run project / Git folder |

Unknown keys are rejected (`additionalProperties: false`).
