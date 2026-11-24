# Session 02: Metric View YAML Library & Manifest

## Scope
Build `src/genie_ontology_sdk/mv_yaml.py` (load, parameter substitution, static validation, DDL rendering) and `src/genie_ontology_sdk/manifest.py` (the forEach `manifest.json`), with tests and fixtures.

## Context
* [L200-E](../../design/L200-E-metric-view-synthesizer.md) YAML generation rules and manifest shape; [L200-F](../../design/L200-F-registration-pipeline.md) testing table.
* [research/metric-view-cicd-best-practices.md](../../research/metric-view-cicd-best-practices.md), [research/semantic-metadata-strategy.md](../../research/semantic-metadata-strategy.md).
* Sample YAML: `examples/metric_views/sales/mv_sales_revenue.yml`. Copy it into `tests/fixtures/metric_views/` and fix it there if it breaks a rule; do not edit `examples/`.
* Parameter tokens are `${source_catalog}`, `${source_schema}`, `${target_catalog}`, `${target_schema}`. They are substituted at registration time. A literal catalog name in `source:` or in a `joins[].source` is a hardcoding error.
* Metric view YAML spec: use the `metric-views` skill for the current `version`, `source`, `joins`, `dimensions`, `measures`, `materialization` keys. Verify against the docs (docSearch "metric view YAML reference"); do not guess keys.
* API contract: [INDEX.md](../INDEX.md#cross-session-contracts).

## Tasks
1. `mv_yaml.py`:
   * `load_mv(path) -> dict`
   * `substitute(text, params) -> str`: fails on any unresolved `${...}`.
   * `validate_mv(doc, *, name) -> list[Finding]`. `Finding` is `{rule, severity: error|warning, message}`. Rules:
     * `MV001` required keys
     * `MV002` unique dimension/measure names
     * `MV003` no wildcard/implicit fields
     * `MV004` parameterized `source:` (no hardcoded catalog)
     * `MV005` every join has an `on`/`using` and, if `rely.at_most_one_match` is set, a `# verified:` comment or the `verified_cardinality` field from EDA (warning if missing)
     * `MV006` comments on every measure (warning)
     * `MV007` a materialization block, if present, has `refresh_policy` and only categorical dimensions listed
   * `render_ddl(doc_text, fq_name, params) -> str`: `CREATE OR REPLACE VIEW <fq> WITH METRICS LANGUAGE YAML AS $$ ... $$`
2. `manifest.py`:
   * `build_manifest(metric_views_dir) -> list[dict]`: entries `{name, yaml_path, domain, subdomain}`, with `yaml_path` relative to the bundle root, sorted by name
   * `write_manifest(...)`
   * `validate_manifest_json(list) -> list[str]`: unique names, files exist
3. Tests: one fixture per rule (good + bad), substitution edge cases, DDL rendering snapshot, manifest ordering and relative paths.
4. A CLI entry point `python -m genie_ontology_sdk.mv_yaml validate <dir>`: prints findings and exits 1 on errors. Session 11 and the gates use it.

## Acceptance Criteria
- [ ] pytest (from a `/tmp` copy) passes; each rule MV001-MV007 has at least one failing and one passing fixture.
- [ ] `python -m genie_ontology_sdk.mv_yaml validate tests/fixtures/metric_views/good` exits 0; `.../bad` exits 1.
- [ ] `render_ddl` output for the sales fixture contains no `${`.

## Owned Paths / Assets
- `src/genie_ontology_sdk/mv_yaml.py`, `src/genie_ontology_sdk/manifest.py`
- `tests/test_mv_yaml.py`, `tests/test_manifest.py`, `tests/fixtures/metric_views/**`

## Dependencies
- Session 01: package layout, `pyproject.toml`, `tests/conftest.py`.
