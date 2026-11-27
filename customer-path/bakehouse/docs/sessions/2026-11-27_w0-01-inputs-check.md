# 2026-11-27 — Wave 0, Session 01: Inputs Check & Report

* Build run: 38498872047824 (job 138308594859344, task `w0_session`), continuation 0, first attempt (no earlier status file for this run).
* Mode: `edit` + `allow_execute`. Workflow `hybrid`, branch `genie-build-bakehouse`.

## What was done

1. Branch check (read-only): Git folder `mbp-bakehouse` is on `genie-build-bakehouse` at `2b524e71183d`. No Git commands run.
2. The session's default compute did not have the SDK installed, so the session installed the published wheel `genie_ontology_modeled_knowledge_sdk-0.1.1-py3-none-any.whl` from the SDK `sdk_wheels` volume into its own scratch Python environment (no workspace or UC change).
3. `config.load_config` + `config.validate_config` on `sdk_config.json`: 0 errors.
4. `config.expand_tables(cfg, WorkspaceClient())`: 4 tables (`samples.bakehouse.sales_customers`, `sales_franchises`, `sales_suppliers`, `sales_transactions`).
5. `config.check_access`: 0 problems. Cross-checked independently with `tables.get` (column counts 12/10/10/10) and `COUNT(*)` (300/48/27/3333 rows).
6. `target_catalog` `hls_fde_dev` exists. `target_schema` `bakehouse_ontology` does not exist yet (informational; the plan checks the catalog only and the schema comes from the metric-views bundle in wave 3). Warehouse `24087b85239cacac` resolves (serverless PRO, stopped). No `supplemental_volume_dirs` or `dashboard_inputs` are configured, so nothing to list.
7. Wrote `docs/inputs_report.md` with sections Config, Source tables, Supplemental inputs, Access problems (`none`), Date.

## Checks

| Check | Result | Detail |
|---|---|---|
| validate_config | pass | 0 errors (installed wheel 0.1.1) |
| expand_tables | pass | 4 tables, all listed in the report (verified by reading the file back) |
| check_access | pass | 0 problems; tables.get + COUNT(*) cross-check |
| inputs_report sections | pass | all 5 sections present; Access problems = `none` |

## Decisions / notes

* `sdk_config.json` was read only, never edited.
* Read-only on Unity Catalog: no CREATE, no grants.
* For later sessions: if your compute lacks the SDK, install the wheel from the SDK `sdk_wheels` volume (`.internal/genie_ontology_modeled_knowledge_sdk-0.1.1-py3-none-any.whl`).

## Files modified

* `docs/inputs_report.md` (created)

## Requests

None.
