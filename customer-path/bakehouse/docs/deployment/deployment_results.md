# Genie Agent Deployment Results

* Build run: 409860738864401 (job 138308594859344), wave 5, session 09. Build run started 2026-11-28T05:05:18Z.
* Bundle: `ontology-genie-agents` (`bundle.name: bakehouse-ontology-genie-agents`), target `dev`, engine `direct`, deployment id `3858229701455671` (version 1), commit `6169665` on `genie-build-bakehouse`.
* Render: `geniespace render agents .rendered --params ../docs/registration/resolved_target.json --check` -> `check: target schema and 3 identifiers resolve`, exit 0.
* `bundle validate --strict --target dev`: Validation OK. `bundle deploy --target dev`: `Created genie_spaces.bakehouse_retail_sales_agent`, 1 created, 0 changed, 0 deleted.

## Agents

| resource key | space id | deploy time (UTC) | probe question | attachment type | query state | error |
|---|---|---|---|---|---|---|
| `bakehouse_retail_sales_agent` | `01f1eaeeac87195fa93d5b083cc91e84` | 2026-11-28T05:43:44Z (space create/update_time) | Which 5 franchises had the highest gross sales? | query | SUCCEEDED | none |

## Probe detail

* `bakehouse_retail_sales_agent`: conversation `01f1eaeeb70913bf95f269e7f88a0902`, message `01f1eaeeb72016138fcbf814b639af0a` (`COMPLETED`). Query attachment `01f1eaeebc071a36ab840ea271bac571` ran `MEASURE(`Gross Sales`)` by `Franchise Name` on `mv_bakehouse_sales`; result `SUCCEEDED`, 5 rows: Baked Bliss 6642, Sweet Sinsations 4512, The Crumbly Nook 2790, Butter Bliss 2514, Golden Crumbs 2502. The top value matches the example SQL result recorded by session 08 (Baked Bliss 6642).
* Title: `[dev matthew_giglia] Bakehouse Retail Sales Agent`; warehouse `24087b85239cacac`.

## agent_probe

**pass**: 1/1 agents answered their first sample question with a `SUCCEEDED` query attachment.
