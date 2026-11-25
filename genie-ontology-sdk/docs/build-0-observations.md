# Build-0 Observations

Consolidated skill gaps, template fixes and platform limits that the build-0 dogfood sessions (10a-16, on `samples.tpch`) reported in their session summaries. Use this list, merged with the owner-accepted [build-1 requests](plans/build-1/REQUESTS.md) (R1-R9), as input when planning build 1. Run, job and space ids are in the linked session summaries, not here.

Types:

* **skill gap**: a `skills/ontology-*` skill is missing a rule, pattern or check.
* **template fix**: a change to SDK code (`src/genie_ontology_sdk/`), a bundle template, the run kit or the TPC-H example.
* **platform limit**: a Databricks platform or tooling behavior the SDK has to work around.

## Dogfood observations (sessions 10a-16)

31 rows: 10a (8), 10b (7), 11 (5), 12 (0), 13 (2), 14 (5), 15 (2), 16 (2). Session 12 reported "Template fixes for build 1: none".

| # | Source session | Observation | Type | Proposed build-1 change |
|---|---|---|---|---|
| 1 | [10a](sessions/2026-11-24_w0-4-10a-tpch-domain-research.md) | Shared dimension tables (`nation`, `region`) conflict with the "each table in exactly one subdomain" rule | skill gap | `ontology-domain-research`: allow a `shared` marker for dimension tables, or give a tie-break rule |
| 2 | 10a | No rule for whether a term's subdomain follows its business meaning or its source table (Revenue is sales, `lineitem` is fulfillment) | skill gap | `ontology-domain-research`: state that terms follow business meaning; list the source table separately |
| 3 | 10a | The `05_domain_subdomain_proposal` template has no `## Sources` section, but the output checklist requires one | template fix | Add `## Sources` to the 05 template in `ontology-domain-research` |
| 4 | 10a | Web search cannot confirm coded column values (`l_returnflag`, `l_linestatus`, `o_orderstatus`) | skill gap | `ontology-domain-research`: defer coded values to the EDA stage and define the hand-over (term file field or request to EDA) |
| 5 | 10a | KPIs whose standard formula needs data the tables lack (SCOR return rate by weight, perfect order) | skill gap | Add a `proxy` convention to `02_kpi_definitions` and the glossary `Data usage` section |
| 6 | 10a | Skill says `readTable` per table; one schema-scoped `information_schema.columns` query was cheaper for 8 tables | skill gap | Allow the scoped `information_schema.columns` query as the default metadata read |
| 7 | 10a | No rule for citing current vs older spec versions (TPC-H v3.0.1 vs v2.x that hold the query text) | skill gap | Add a citation rule: cite the current version, plus the older one when it holds the referenced text |
| 8 | 10a | One file per term costs two tool calls (create + edit); 28 outputs took about 56 calls, a step-limit risk | platform limit | Add a bulk-write helper (e.g. `pages.write_terms`) or document an allowed bulk pattern in the skill |
| 9 | [10b](sessions/2026-11-24_w0-4-10b-tpch-deep-eda.md) | Pattern F usage uses `LIKE '%<schema>.<table>%'`, so `part` also matches `partsupp` | skill gap | `ontology-deep-eda`: use a word-boundary regex (`rlike '<schema>\\.<table>([^a-z0-9_]\|$)'`) |
| 10 | 10b | Pattern E lineage on shared sources returns other users' downstream tables | skill gap | `ontology-deep-eda`: report lineage counts only, never names (no-identifiers rule) |
| 11 | 10b | No reverse-direction orphan check (right keys never referenced, e.g. customers without orders) | skill gap | Add "pattern D2: unreferenced right keys" with a `LEFT ANTI JOIN` |
| 12 | 10b | Extracting common filter/join columns from usage samples is underspecified; a key-lookup-heavy sample produced none | skill gap | Define a parser, or skip the step when the sample is not diverse |
| 13 | 10b | `hot_table` "top quartile" is ambiguous on 8 tables | skill gap | State the rounding rule (e.g. `ceil(n / 4)`) |
| 14 | 10b | No rule for which columns count as sensitive beyond examples (`o_clerk`, `p_name` withheld) | skill gap | Add a sensitive-column rule (name patterns + free text), with values withheld by default |
| 15 | 10b | `DESCRIBE HISTORY LIMIT 20` can show only VACUUM commits, hiding the last data write | skill gap | Filter out maintenance operations when deriving update cadence |
| 16 | [11](sessions/2026-11-24_w0-5-11-tpch-mv-synthesis.md) | No verified pattern for share-of-total KPIs (national market share); the view exposes only `Market Volume` | skill gap | Verify a share-of-total pattern on the platform and add it to `ontology-mv-synthesis/references/yaml-patterns.md` |
| 17 | 11 | Snowflake dimensions must be referenced by the full join path (`orders.customer.customer_nation.n_name`); not documented | skill gap | Add a nested-join example to `yaml-patterns.md` |
| 18 | 11 | Materialization thresholds (>= 3 joins or >= 10M rows) are met by almost every star-schema view | skill gap | Rank candidates or cap materialization blocks per domain |
| 19 | 11 | No rule for a KPI with two candidate formulas (AOV header vs line basis, on-time ship vs receipt) | skill gap | Document distinct measure names per basis plus an owner decision note |
| 20 | 11 | Synthesis checks are static only; nested joins, `FILTER` measures and materialization are first tested at registration | skill gap | Add an optional platform dry run (register into a scratch schema, or `EXPLAIN` the rendered DDL) |
| 21 | [13](sessions/2026-11-24_w0-7-13-tpch-uc-pages.md) | `upsert_pages` without `domain_id` matches titles account-wide, so common terms collide with other teams' pages | template fix | `pages.py`: require `domain_id` for live runs, or scope title matching to the term's front-matter domain (covered by R4) |
| 22 | 13 | Page descriptions are truncated at 160 characters mid-link for 3 terms | template fix | `pages._first_sentence`: strip markdown links before truncating |
| 23 | [14](sessions/2026-11-24_w0-7-14-tpch-agent-curation.md) | Workspace file tools cannot create `*.geniespace.json`; unattended sessions need the import API | platform limit | Document the import-API path in `ontology-agent-curation`, or add a `geniespace write` CLI |
| 24 | 14 | `write_domain_manifest` for a single-agent plan collapses the subdomains into one named after the domain | template fix | `geniespace.py`: list the real subdomains with the same agent |
| 25 | 14 | `render_space_text` accepts only full JSON documents; one SQL string cannot be resolved for `EXPLAIN` | template fix | Add a token-substitution helper (e.g. `geniespace.render_text`) |
| 26 | 14 | The skill does not check that the overrides' `catalog`/`schema` match where DAB 1 registered the views | skill gap | `ontology-agent-curation`: add an `information_schema` check before `EXPLAIN` |
| 27 | 14 | No rule for the template placeholder agent (delete vs keep) given the no-deletion rule | skill gap | Have the scaffold or curation step replace the placeholder, or state that the owner deletes it |
| 28 | [15](sessions/2026-11-25_w0-8-15-tpch-agent-deployment.md) | The DAB 1 dev schema and the agents bundle `schema` are set by hand in two places and drifted (blocked wave 0-8 once) | template fix | Derive the agents bundle `schema` from DAB 1, or have the render step check `information_schema` and fail when it is missing (covered by R4) |
| 29 | 15 | The render CLI fails only on unresolved tokens, not on identifiers that do not resolve | template fix | `geniespace render`: optional `--check` that resolves the target schema and every identifier |
| 30 | [16](sessions/2026-11-25_w0-9-16-tpch-tuning.md) | q11 miss: Genie returned `100 * Return Rate` (24.69) against 0.2469; ratio unit ambiguity | template fix | TPC-H metric views: percentage `format` and a "fraction 0-1" comment on `Return Rate` / `Return Line Rate`, then re-register |
| 31 | 16 | `benchmark.score` counts a x100 match of a 0-1 ratio as a miss | template fix | `benchmark.score`: report it as `unit_mismatch` |

## Owner and process items (not counted above)

| Source session | Item | Build-1 change |
|---|---|---|
| [12](sessions/2026-11-24_w0-6-12-tpch-mv-registration.md) | The first run blocked: `bundle.deploy` was approved but the `register_metric_views` job run was not | Run kit authorizations name the job run explicitly (R3) |
| 13 | UC Pages need a Discover domain; none exists for TPC-H, and the plan forbids creating one. Pages were not written (dry run only) | Owner creates or chooses a domain, then runs the owner cell in `examples/tpch/docs/pages/pages_registration.md`; run kit plan 07 must not run the live upsert without a domain (R3) |
| 14, 15 | Unreferenced template placeholder `ontology-genie-agents/agents/ontology_agent.geniespace.json` remains in `examples/tpch/` | Owner deletes it, or the scaffold stops copying it once an agent exists |
| 16 | Baseline accuracy 93.3% (15 questions) passed the 70% gate; no tuning iteration ran | None required; rows 30-31 hold the proposed fixes |

## Earlier build-0 sessions (01-09)

Notes from the SDK-building sessions that also affect build 1. They are not part of the dogfood count.

| Source session | Observation | Type | Proposed build-1 change |
|---|---|---|---|
| [06](sessions/2026-11-24_w0-2-06-mv-bundle-template.md) | `warehouse_id` is required by the metric-views template but no task uses it (all serverless notebooks) | template fix | Make it optional or use it for an ad hoc check task |
| [07](sessions/2026-11-24_w0-2-07-agent-bundle-template.md) | `genie_spaces` `file_path` JSON is not interpolated by the bundle CLI; agent files are rendered into gitignored `.rendered/` | platform limit | Keep the render step; drop it if the CLI starts interpolating space files |
| 07 | `file_path` resolves relative to the YAML file that declares it, not the bundle root | platform limit | Documented in the template README; keep a test for it |
| [08](sessions/2026-11-24_w0-2-08-run-kit.md) | The gate's `/tmp` pytest copy cannot find genie-build-waves, so the `validate_manifest` test skips | template fix | Set `GENIE_BUILD_WAVES_DIR` in the gate command or vendor the validator (R3, R5) |
| [09](sessions/2026-11-24_w0-3-09-init-and-tpch-scaffold.md) | A gate that greps `git ls-files` for `variable-overrides.json` matches the session 03 test fixture | template fix | Scope the gate check to `examples/` or `.databricks/` paths |
| 09 | The init notebook's default `target_catalog` (`main`) is not accessible in every workspace | template fix | Leave the default empty and require the user to set it (R6) |
