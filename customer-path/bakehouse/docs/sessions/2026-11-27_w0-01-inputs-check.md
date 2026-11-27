# 2026-11-27 — Wave 0, Session 01: Inputs Check & Report

Run `531733719859424`, mode `edit` (allow_execute), branch `genie-build-bakehouse` (verified read-only via Repos API, head `16032380a4fb`).

## What was done

* Installed SDK wheel `genie_ontology_modeled_knowledge_sdk` `0.1.1` into the session's ephemeral Python env from `mbp/genie-ontology-modeled-knowledge-sdk/dist/` (not vendored; not installed by default on serverless).
* `load_config(sdk_config.json)` + `validate_config` -> 0 errors.
* `expand_tables(cfg, WorkspaceClient())` -> 4 tables: `samples.bakehouse.sales_customers` (12 cols, 300 rows), `sales_franchises` (10, 48), `sales_suppliers` (10, 27), `sales_transactions` (10, 3333).
* `check_access` -> no problems. Cross-checked independently with `ws.tables.get` and a read-only `COUNT(*)` per table (all succeeded).
* Target catalog `hls_fde_dev` exists. Target schema `hls_fde_dev.bakehouse_ontology` does not exist yet (informational; expected to be created by the metric-views bundle in wave 3).
* No `supplemental_volume_dirs` / `dashboard_inputs` configured.
* Wrote `docs/inputs_report.md` with sections Config, Source tables, Supplemental inputs, Access problems (`none`), Date.

## Decisions

* Treated the missing target schema as informational, not an access problem: the plan checks only `target_catalog`, and no `CREATE` is allowed in this session.

## Checks

| Check | Result |
|---|---|
| `validate_config` 0 errors | pass |
| Report lists every expanded source table | pass |
| `## Access problems` says `none` | pass |
| Report has all 5 required sections | pass |

## Files modified

* `docs/inputs_report.md` (created)

## Requests

None. Note for session 03: no supplemental inputs, so it should take the no-inputs path.
