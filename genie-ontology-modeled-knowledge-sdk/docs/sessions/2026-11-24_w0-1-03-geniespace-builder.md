# 2026-11-24 — Wave 0-1 / Session 03: Genie Agent Config Builder

* Build run: job `419885870201924`, run `701596191246320`, task `w0-1_session`, continuation 0
* Mode: `edit` (`allow_execute: true`), workflow `hybrid`, branch `mg-genie-ontology-modeled-knowledge-sdk` (verified read-only via the Repos API; head `9393658e854a`)
* Status: **pass**

## Changes

| File | What |
|---|---|
| `src/genie_ontology_sdk/geniespace.py` | `MvRef`, `AgentPlan`, `mv_refs_from_manifest`, `plan_agents`, `stable_id`, `build_space`, `space_to_json`, `validate_space`, `domain_manifest`, `write_domain_manifest`, `normalize_params`, `render_space_text`, `render_space_file`, `render_dir`, CLI `main` (`render <src_dir> <dst_dir> --params <json>`) |
| `tests/test_geniespace.py` | 20 test functions (29 collected with parametrization) |
| `tests/fixtures/geniespace/variable-overrides.json` | Bundle-overrides-shaped params with placeholder values (`main`, `ontology_tpch`, dummy warehouse id) |

`tests/fixtures/geniespace/tokenized/` is an empty folder: the workspace file API rejects creating `*.geniespace.json` files ("node type [UNKNOWN] is not supported"), so tests generate the tokenized space with `build_space` into `tmp_path` instead. Git does not track the empty folder.

## Decisions

* **Planning (L200-G).** `<= max_per_agent` MVs -> one agent `<domain>_agent` (`subdomain: None`). Otherwise one agent per subdomain (`<domain>_<subdomain>_agent`; MVs without a subdomain -> `general`). A subdomain larger than the limit is chunked into `<domain>_<subdomain>_<n>_agent`. Each MV is in exactly one agent; cross-domain MVs follow their subdomain; the agent domain is the most common MV domain. Split agents list each other in `related_agents` (for pointer instructions in curation). Duplicate MV names and `max_per_agent < 1` raise `ValueError`.
* **Identifiers.** `MvRef.identifier` = `fq_name` or `${target_catalog}.${target_schema}.<name>`. Metric views go into `data_sources.tables` as the plan says (the docs also list a `data_sources.metric_views` array; `validate_space` counts both).
* **Determinism.** Ids are `uuid5(fixed namespace, text).hex` (32 lowercase hex). Sample questions, example SQLs and join specs are sorted by id, tables by identifier, all dict keys sorted; `space_to_json` = `json.dumps(indent=2, sort_keys=True)` + newline. Same plan twice -> byte-identical; MV input order does not matter.
* **Text instructions** are one entry holding de-duplicated lines (whitespace/case-insensitive), kept minimal per L200-H Phase 2. Sample questions and example questions are de-duplicated the same way. Example `sql` strings are split into lines with line endings, matching the sample file.
* **`warehouse_id`** is not part of the serialized space (the bundle `genie_spaces` resource sets it). `build_space` accepts it for call-site symmetry and only type-checks it.
* **Validation.** version 2; 1-30 data sources; 3-part, unique identifiers; sample-question ids unique 32-hex with non-empty question; instruction ids 32-hex; no duplicate text-instruction lines. Returns a list of messages.
* **Rendering.** Tokens `${target_catalog}`, `${target_schema}`, `${warehouse_id}`; params accept token names or bundle `variable-overrides.json` keys (`catalog`, `schema`, `warehouse_id`; explicit token names win). Values are JSON-escaped, output must parse as JSON, and any unresolved `${...}` raises (CLI exit 1). `render_dir` checks every file before writing any, so a failure leaves `dst_dir` untouched.
* **Domain manifest.** L200-G YAML shape (`domains[].subdomains[] {name, description?, metric_views, agent, related_agents?}`); a single-agent plan is listed as one subdomain named after the domain.

## Design note for later sessions (05b, 07, 14)

`max_metric_views_per_agent` defaults to 50, but `validate_space` (per this plan's 1-30 rule; the Genie product limit itself was not re-verified in this session) allows at most 30 data sources per agent. An agent with 31-50 MVs passes `plan_agents` but fails `validate_space`. Session 14 (curation) should call `plan_agents(mvs, max_per_agent=min(cfg.max_metric_views_per_agent, 30))`, or the owner should revisit the 50 default. Not changed here (outside scope).

## Checks

| Check | Result |
|---|---|
| Gate pytest (`/tmp` copy, `python -m pytest -q`) | pass — 60 passed (whole suite at run time) |
| `tests/test_geniespace.py` has >= 8 tests | pass — 29 collected |
| `examples/agents/sales_agent.geniespace.json` passes `validate_space` | pass — no errors (`test_sales_example_passes_validation`) |
| Same plan built twice -> byte-identical JSON | pass (test + separate CLI-side script) |
| `python -m genie_ontology_sdk.geniespace render` with overrides params: no `${` left, exit 0; missing token: exit 1 | pass (tests + manual run on a tokenized copy of the sales example) |
| No workspace-specific values in owned files | pass — grep found none |

## Requests

None. See the design note above for session 14 / owner.
