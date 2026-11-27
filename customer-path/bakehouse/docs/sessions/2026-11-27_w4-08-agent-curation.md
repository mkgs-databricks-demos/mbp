# 2026-11-27 — Wave 4, Session 08: Genie Agent Curation

* Build run: 38498872047824 (job 138308594859344, task `w4_session`), continuation 0, first attempt.
* Mode: `edit` + `allow_execute` (no deploy). Workflow `hybrid`, branch `genie-build-bakehouse` (Git folder `mbp-bakehouse` confirmed on that branch at `9ef83bc wave(3): 06` with a read-only `git rev-parse`; no state-changing Git commands).

## What was done

1. Skills: the UC skill `hls_fde_dev.dev_matthew_giglia_ontology_sdk.genie_build_session_runner` and the UC `ontology-agent-curation` skill (hyphen and underscore names tried) did not resolve through `readSkillFile`. Used the workspace fallbacks: `mbp-bakehouse/genie-build-waves/src/skills/genie-build-session-runner/SKILL.md` and `mbp/genie-ontology-modeled-knowledge-sdk/skills/ontology-agent-curation/SKILL.md`.
2. Context read: manifest (wave 4, session 08), plan `plans/08_agent_curation.md`, `PROJECT_MEMORY.md`, `sdk_config.json`, session 05 and 06 summaries, `docs/registration/registration_results.md` and `resolved_target.json`, `metric_views/manifest.json`, the three metric view YAMLs (measure/dimension names, comments), the KPI table in `docs/research/02_kpi_definitions.md`, `05_domain_subdomain_proposal.md`, `docs/context/00_source_inventory.md` (no supplemental inputs) and the joins table in `docs/data_profiles/data_model_summary.md`. The two research docs were read only in part (the KPI table and subdomain table); all content used here comes from those parts.
3. SDK wheel `genie_ontology_modeled_knowledge_sdk-0.1.1` installed from the SDK checkout `dist/` into the session's serverless Python env only.
4. Planned agents with `geniespace.plan_agents(mvs, max_per_agent=30)` over the 3 registered views (all 3 manifest entries are registered per `registration_results.md`). `effective_max_per_agent(30)` = 30, so the result is **one agent**: `bakehouse_retail_sales_agent` (no subdomain, no related agents).
5. Built the space with `build_space`, validated with `validate_space` (0 errors), and wrote it with the workspace import API (`format: RAW`, overwrite), as the curation skill says to, because the file editor cannot create `*.geniespace.json`. The sha256 of the read-back file matched the `space_to_json` text, and `validate_space` on the read-back returned 0 errors.
6. Replaced the template `ontology_agent` entry in `resources/genie_agents.yml` with `bakehouse_retail_sales_agent` (same warehouse, parent path and permissions; `file_path: ../.rendered/bakehouse_retail_sales_agent.geniespace.json`). No placeholder agent file existed in `agents/` (only `.gitkeep`), so there was nothing to delete.
7. Generated `docs/domain_manifest.yml` with `geniespace.write_domain_manifest(plans, <scratch path>, descriptions=...)` (descriptions from `05_domain_subdomain_proposal.md`), then wrote the same text with the workspace file tools.
8. Ran the README render step: `geniespace render agents .rendered --params ../docs/registration/resolved_target.json --check`. In a shell subprocess this failed with an auth error (`default auth: runtime: 'NoneType' object has no attribute 'parent_header'`, nothing written). The same CLI run in-process in the Python session (`runpy`, same args) exited 0: `check: target schema and 3 identifiers resolve`. That produced `.rendered/bakehouse_retail_sales_agent.geniespace.json` (gitignored).
9. `bundle validate --strict --target dev` for `ontology-genie-agents`: `Validation OK!`.

## Agent content

* **Data sources (3):** `${target_catalog}.${target_schema}.mv_bakehouse_customer_activity`, `.mv_bakehouse_sales`, `.mv_bakehouse_supplier_coverage`.
* **Sample questions (8),** from the `02_kpi_definitions.md` KPI table: gross sales and units by product (Gross Sales, Units Sold); ATV and UPT by franchise country; payment method share (Payment Method Mix); top 5 franchises by gross sales (Gross Sales, franchise breakdown); latest week vs prior week (period comparison); average selling price by product; revenue per customer, purchase frequency and repeat customer rate by customer country; share of franchises with a supplier and franchises on an approved supplier (Supplier Coverage, Approved Supplier Share).
* **Text instructions (2):**
  * Use `mv_bakehouse_customer_activity` for revenue per customer, purchase frequency, repeat customer rate and customer coverage, and do not derive them from `mv_bakehouse_sales`. Reason: `mv_bakehouse_sales` also has `Customers with Purchases` and customer geography, which invites a second, time-sliced derivation that differs from the governed customer-grain measures. This choice of view cannot be stated inside a single metric view.
  * When supplier coverage or approved supplier share is asked without a basis, show both the franchise-basis and supplier-basis measures and name each basis. Reason: session 05 left the two-formula choice as an owner decision. The views expose both bases, so the ambiguity remains open.
* **Example SQL (2, multi-step only):** top 5 franchises by `MEASURE(`Gross Sales`)` (ranking), and latest vs prior week of gross sales (CTE + `LAG`, period over period). Both passed `EXPLAIN` and ran against the resolved dev schema. Top 5: Baked Bliss 6642 first. Latest week 2024-05-13: 17715 vs 28509, -37.9%. The latest week is partial (the data spans 17 days per session 05), so this example returns a partial-week comparison.
* **Join specs:** none. The three views have different grains (transaction, customer, franchise). The verified joins in `data_model_summary.md` are between source tables and are already inside the views' YAML (or, for customer activity, inside its SQL source). No question in the sample set needs a cross-view join.

## Domain manifest (proposal only)

`docs/domain_manifest.yml`: domain `bakehouse_retail_sales`, subdomains `customers`, `franchise_supply`, `sales`, each with one metric view and all pointing at `bakehouse_retail_sales_agent`. This is a proposal. Creating UC domains/subdomains is opt-in for the owner, and no domain API was called.

## Checks

| check | result |
|---|---|
| branch is `genie-build-bakehouse` | pass |
| agent count follows rule (3 views <= 30 -> 1 agent, from `plan_agents`) | pass |
| `validate_space` on built and read-back file | pass (0 errors) |
| import-API write, sha256 read-back match | pass |
| no literal catalog/schema/warehouse id in agent file (`hls_fde_dev`, `dev_matthew_giglia_bakehouse_ontology`, warehouse id, `samples.`, `hls_fde`) | pass |
| every referenced view registered (`registration_results.md`) | pass (3/3) |
| example SQL `EXPLAIN` + run on resolved schema | pass (2/2) |
| render `--check` with `resolved_target.json` | pass (in-process; shell subprocess auth failure noted) |
| `bundle validate --strict --target dev` (ontology-genie-agents) | pass |

## Files

* `ontology-genie-agents/agents/bakehouse_retail_sales_agent.geniespace.json` (new)
* `ontology-genie-agents/resources/genie_agents.yml` (placeholder entry replaced)
* `docs/domain_manifest.yml` (new)
* Generated, gitignored, not committed: `ontology-genie-agents/.rendered/bakehouse_retail_sales_agent.geniespace.json` (output of the plan-mandated render step).

## Requests / notes for later sessions

* Session 09: run the render in a context with workspace auth. In this serverless env the shell-subprocess form of the render CLI failed auth, and the in-process Python form worked.
* Owner decisions carried from session 05 are still open (Supplier Coverage basis, Approved Supplier Share basis, Customer Gender exposure). The second text instruction can be removed once the basis is decided and encoded in the view.
