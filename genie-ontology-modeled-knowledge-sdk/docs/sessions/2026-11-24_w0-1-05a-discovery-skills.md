# 2026-11-24 — Wave 0-1, Session 05a: Discovery Skills (Research, Context, EDA)

* Job run: 701596191246320 (task `w0-1_session`, continuation 0)
* Branch: `mg-genie-ontology-modeled-knowledge-sdk` (verified read-only on the `mbp` Git folder before any edit)
* Mode: `edit` (no execution allowed; checks done by reading and workspace regex search)
* Status: **pass**

## Scope

All tasks in plan `build-0/05a_discovery_skills.md`: three Genie Code skills for pipeline-run stages 1-3.

## Changes

| File | Content |
|---|---|
| `skills/ontology-domain-research/SKILL.md` | 10-search budget and plan (terminology, KPIs, regulatory, benchmarks, reserve), stop rules, citation rule, research doc template for `docs/research/01`-`04`, `05_domain_subdomain_proposal.md` template (proposal only, opt-in creation), glossary term file format in `docs/semantics/<term_slug>.md` with the INDEX front matter contract, output checklist |
| `skills/ontology-context-extraction/SKILL.md` | clean no-inputs path (inventory only = pass; all paths unreadable = blocked), inventory template, per-type readers (md, `ai_parse_document` for pdf/docx/pptx with a SQL pattern, csv/xlsx, json), Tableau XML and Power BI (`.pbit` / `model.bim` / TMDL; `.pbix` skipped, export requested) hints, context doc template (rules, KPI formulas, joins, filters, hierarchies), glossary candidates in `docs/context/glossary_candidates/`, output checklist |
| `skills/ontology-deep-eda/SKILL.md` | sampling rules for > 10M rows (`TABLESAMPLE (1 PERCENT) REPEATABLE (42)` for null rates/distributions, `approx_count_distinct` for distinct, exact full-table grain and cardinality), per-table checklist with SQL patterns A-C (null/distinct, top values, grain), cross-table patterns D (orphan rate) and G (runnable cardinality verification + decision table), system-table lineage (E) and usage (F) queries with a no-retry fallback on access errors, materialization signals, profile template, `data_model_summary.md` template with the contract join table, output checklist |

## Decisions

* Glossary files are one per term, `<term_slug>` = snake_case term (INDEX contract says `docs/semantics/<term>.md`; the l300 reference plan's "one file per subdomain cluster" is superseded). Body headings are `## Definition`, `## Business context`, `## Data usage`, matching the INDEX contract casing.
* Join orientation: `left` = many side, `right` = one side, so the contract's three values (`many_to_one`, `one_to_one`, `many_to_many`) cover all cases; a one-to-many result is swapped and re-run.
* Approx cardinality fallback is recorded with `(approx)` in `query_used`, and synthesis is told not to set `rely.at_most_one_match` on it (MV005 then warns).
* Context extraction budgets: 50 files, 20 pages per document by default.
* Examples use only public `samples.tpch` names and `<placeholders>`.

## Checks

| Check | Result | How |
|---|---|---|
| Three SKILL.md files, front matter `name` = folder | pass | regex search: `name: ontology-domain-research`, `-context-extraction`, `-deep-eda` on line 2 of each |
| `description` < 500 characters | pass | by reading; each is about 320-345 characters |
| Output paths match INDEX run layout | pass | regex search for `docs/(plans\|registration\|pages\|deployment\|tuning\|sessions\|design)/` in `skills/`: 0 hits; skills write only `docs/research/`, `docs/semantics/`, `docs/context/`, `docs/data_profiles/` |
| EDA has runnable cardinality SQL + sampling rule | pass | pattern G and the Sampling rules section (regex hit on `TABLESAMPLE`) |
| No workspace-specific identifiers | pass | regex search for hosts, user names, `hls_fde`, 12+ digit ids in `skills/`: 0 hits (positive control search returned the expected 3 files) |
| SQL patterns executed | skipped | edit session without `allow_execute`; patterns not run against a warehouse. Session 10b (TPC-H deep EDA) is the first live run |

## Requests / notes for other sessions

* 04 (`pages.parse_glossary`): skills write front matter `term`, `synonyms`, `domain`, `subdomain`, `related_terms`, `sources` and headings `## Definition`, `## Business context`, `## Data usage`. Glossary candidates from context extraction live in `docs/context/glossary_candidates/` with the same format; session 13 (UC Pages) may need to read both folders.
* 02 (`mv_yaml` MV005): the join table is in `docs/data_profiles/data_model_summary.md` under `## Joins`, columns `left | right | keys | verified_cardinality | orphan_rate | query_used`.
* 08 (run kit): the run plans for waves 1-3 can load these skills by name and use their Output checklist sections as pass criteria.

## Files modified

* `skills/ontology-domain-research/SKILL.md` (new)
* `skills/ontology-context-extraction/SKILL.md` (new)
* `skills/ontology-deep-eda/SKILL.md` (new)
