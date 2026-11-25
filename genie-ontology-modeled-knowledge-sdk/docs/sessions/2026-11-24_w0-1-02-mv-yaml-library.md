# 2026-11-24 — Wave 0-1 / Session 02: Metric View YAML Library & Manifest

* Build run: job `419885870201924`, run `701596191246320`, task `w0-1_session`, continuation 0
* Mode: `edit` (`allow_execute: true`), workflow `hybrid`, branch `mg-genie-ontology-modeled-knowledge-sdk` (verified read-only with `git rev-parse`)
* Status: **pass**

## Changes

| File | What |
|---|---|
| `src/genie_ontology_sdk/mv_yaml.py` | `load_mv`, `load_mv_text`, `substitute`, `find_tokens`, `validate_mv(doc, *, name, text=None)`, `validate_file`, `validate_path`, `has_errors`, `render_ddl`, `strip_sdk_only_keys`, `iter_mv_files`, `Finding`; CLI `python -m genie_ontology_sdk.mv_yaml validate <dir-or-file> [--quiet]` |
| `src/genie_ontology_sdk/manifest.py` | `build_manifest(metric_views_dir, *, bundle_root=None)`, `write_manifest(entries, path, *, base_dir=None)`, `validate_manifest_json(entries, *, base_dir=None)`; CLI `python -m genie_ontology_sdk.manifest build <metric_views_dir> <out.json> [--bundle-root]` |
| `tests/test_mv_yaml.py` | Fixture-driven + inline tests for MV001-MV007, substitution, DDL snapshot, CLI (in-process and `python -m`) |
| `tests/test_manifest.py` | Ordering, relative POSIX paths, domain/subdomain, error cases, write round trip, CLI |
| `tests/fixtures/metric_views/good/**` | 3 clean MVs: `sales/mv_sales_revenue.yml` (copy of the example), `sales/mv_sales_returns.yml` (SQL source + CTE + `using`), `tpch_supply_chain/orders/mv_tpch_order_lines.yml` (nested joins, `fields`, `verified_cardinality`) |
| `tests/fixtures/metric_views/bad/**` | One error fixture per rule MV001, MV002, MV003, MV004, MV005, MV007 (x2) |
| `tests/fixtures/metric_views/warn/**` | Warning-only fixtures MV005 (unverified rely), MV006 (measure without comment) |

## Rules

| Rule | Severity | Checks |
|---|---|---|
| MV001 | error (unknown column keys: warning) | view name is an identifier; known top-level keys only; `version` 0.1/1.1 (bare `1` rejected); `source`; at least one of `dimensions`/`fields`/`measures`; not both `dimensions` and `fields`; every column has `expr`; every join has `name` + `source` |
| MV002 | error | dimension/measure names unique (case-insensitive); join names unique and not `source`; parameter names do not collide; cross-file duplicate MV names in the CLI |
| MV003 | error | no `.*` / `*` / `* EXCEPT` field exprs; every field has an explicit `name`; no `SELECT *` in SQL sources |
| MV004 | error (literal schema: warning) | `source` and every (nested) `joins[].source`, including table refs inside SQL sources (CTE names skipped), are 3-part with a `${...}` catalog; only the four known tokens |
| MV005 | error / warning | every join has `on` or `using` (not both); `rely.at_most_one_match` needs a `# verified:` comment in the join item (or on the line above it) or a `verified_cardinality` field, else warning |
| MV006 | warning | every measure has a non-blank `comment` |
| MV007 | error | `mode: relaxed`; non-empty `materialized_views`; each has `name`, valid `type`, `refresh_policy` (auto / incremental / incremental strict / full; needs version 1.1); listed dimensions exist, are not measures, not `*`, and are categorical (not number/currency/percentage/byte format, not window, not id/key-like); listed measures exist or are `*`; one unaggregated max (no dims/measures); not `cluster_by` + `partition_by`; no `parameters` with materialization |

## Decisions

* **YAML 1.2 booleans.** PyYAML (YAML 1.1) loads the join key `on:` as `True`. `load_mv_text` uses a `SafeLoader` subclass where only `true`/`false` are booleans. MV005 also accepts a `True` key for dicts parsed with plain `yaml.safe_load`. Downstream sessions should load MV YAML with `mv_yaml.load_mv` / `load_mv_text`, not `yaml.safe_load`.
* **`validate_mv` accepts dict or text.** The `# verified:` comment is not in the parsed dict, so `validate_mv` takes an optional `text=` (or raw text as `doc`). `validate_file` and the CLI pass the text.
* **`verified_cardinality` is SDK-only.** The metric view spec does not define it, so `render_ddl` strips `verified_cardinality:` lines before registration (comments are kept).
* **`substitute` is strict.** Any leftover `${...}` (including `${}`, `${ x }`, unterminated `${x`) raises; values must be identifiers or backtick-quoted (SQL injection guard); single pass.
* **`render_ddl`** substitutes tokens in `fq_name` too, requires a 3-part name, rejects a body containing `$$`, checks the result still parses, and emits `CREATE OR REPLACE VIEW <fq>\nWITH METRICS\nLANGUAGE YAML\nAS $$\n<body>$$`.
* **Manifest subdomain.** The MV spec has no subdomain key: `subdomain` comes from a `# subdomain: <name>` header comment, else a second folder level (`metric_views/<domain>/<subdomain>/`), else `null`. `domain` is the first folder; YAML files directly in `metric_views/` are an error. `yaml_path` is relative to the bundle root (default: parent of `metric_views_dir`).
* **CLI exit codes:** 0 = no errors (warnings allowed), 1 = errors or no YAML files found, 2 = path does not exist.

## Checks

| Check | Result |
|---|---|
| Gate pytest from `/tmp/gos-gate` copy (`pip install -q pyyaml jsonschema pytest && python -m pytest -q`) | pass — 210 passed (whole suite incl. other wave 0-1 sessions' tests present at the time) |
| Each rule MV001-MV007 has a failing and a passing fixture/test | pass (`test_fixture_dirs_cover_every_rule`, per-rule tests) |
| `PYTHONPATH=src python -m genie_ontology_sdk.mv_yaml validate tests/fixtures/metric_views/good` | pass — exit 0, 3 files, 0 errors, 0 warnings |
| `... validate tests/fixtures/metric_views/bad` | pass — exit 1, 9 errors across 7 files |
| `render_ddl` on the sales fixture has no `${` | pass |
| `import genie_ontology_sdk.config, .mv_yaml, .manifest` | pass |

## Notes for later sessions

* **`examples/metric_views/sales/mv_sales_revenue.yml`** validates with 1 warning (MV005, no `# verified:`), but `render_ddl` rejects it because its header comment contains `$$ <this file> $$`, which would end the DDL body. The test copy uses `$ ... $`. Session 11 / templates must not put `$$` in MV YAML (comments included). `examples/` was not edited (plan rule).
* **Session 06 (MV bundle template):** generate the forEach input with `python -m genie_ontology_sdk.manifest build metric_views manifest.json` (from the bundle root) and render each entry with `render_ddl(open(yaml_path).read(), f"{catalog}.{schema}.{name}", params)`. The registration notebook should catch `ValueError` from `substitute` / `render_ddl`.
* **Session 11 (synthesis):** put `# verified: <evidence>` inside each join item that sets `rely.at_most_one_match` (or a `verified_cardinality:` key), a `# subdomain:` header for the manifest, and `refresh_policy: auto` on every materialized view.

## Requests

None.
