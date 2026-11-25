# Session 24 (wave 1-2): Discovery Skills — Reconcile & Close Gaps (R8)

* Run: `109257611554257` | Mode: edit | Branch: `mg-genie-ontology-build-1-plan` (verified read-only)
* Plan: `docs/plans/build-1/24_discovery_skills.md` | Depends on: 20 (`pages.write_terms`, pass)

## Changes

* `skills/ontology-domain-research/SKILL.md`: stage-named description; schema-scoped metadata read; spec citation rule; platform skills section; proxy KPI convention; `## Shared dimensions` + tie-break and `## Sources` in the 05 template; business-meaning subdomain rule with `Source tables:` line; `## Values from EDA` hand-over; bulk writes via `pages.write_terms`; checklist updated.
* `skills/ontology-deep-eda/SKILL.md`: stage-named description; installed-package wording; sensitive-column rule; platform skills section; pattern D2; lineage counts only; word-boundary usage regex; usage-diversity rule; pattern H cadence; `hot_table` rounding; `## Coded values` profile section; checklist updated.
* `skills/ontology-context-extraction/SKILL.md`: reconcile only (description, platform skills section, `ai_parse_document` SQL replaced by a pointer to `sql-functions`, BI hints point to `bi-migration`).

## Observations closed (file / section)

| Obs | File | Section |
|---|---|---|
| 1 shared dimensions | ontology-domain-research | Domain/subdomain proposal: `## Shared dimensions` + Table assignment rules (shared marker, tie-break) |
| 2 business meaning vs source table | ontology-domain-research | Glossary term files: Rules (subdomain follows business meaning; `Source tables:` line in `## Data usage`) |
| 3 `## Sources` in 05 | ontology-domain-research | Domain/subdomain proposal template + Output checklist |
| 4 coded values deferred to EDA | ontology-domain-research + ontology-deep-eda | Glossary Rules and `## Values from EDA` section; EDA Table profile `## Coded values` and checklist |
| 5 proxy convention | ontology-domain-research | Proxy KPIs (02 `proxy` column, `Proxy:` line in `## Data usage`) |
| 6 schema-scoped metadata read | ontology-domain-research | Inputs (default `information_schema.columns` query) |
| 7 spec version citation | ontology-domain-research | Guardrails: Spec versions |
| 8 bulk term writes | ontology-domain-research | Glossary term files: `pages.write_terms` example and fallback |
| 9 word-boundary usage regex | ontology-deep-eda | Pattern F (`rlike '<schema>\\.<table>([^a-z0-9_]\|$)'`) |
| 10 lineage counts only | ontology-deep-eda | Pattern E: lineage counts; profile `## Lineage` |
| 11 unreferenced right keys | ontology-deep-eda | Pattern D2 (`LEFT ANTI JOIN`), Cross-table checklist step 2 |
| 12 usage sample diversity | ontology-deep-eda | Pattern F: skip extraction below 5 distinct query shapes, and say so |
| 13 `hot_table` rounding | ontology-deep-eda | Materialization signals: top `ceil(n / 4)` |
| 14 sensitive columns | ontology-deep-eda | Guardrails: Sensitive columns (name tokens + free text, values withheld) |
| 15 maintenance ops in history | ontology-deep-eda | Per-table checklist row 7 + Pattern H |

## Platform skill overlap (input for session 26, `skills/README.md`)

| SDK skill | Platform skills it relies on | Removed / not restated | Precedence |
|---|---|---|---|
| ontology-domain-research | `discover-pages` | none restated; stage never creates pages (UC Pages stage uses `pages.upsert_pages`) | SDK file contracts win in an SDK run; `discover-pages` for general page work |
| ontology-context-extraction | `sql-functions`, `bi-migration`, `writing-sql` | full `ai_parse_document` SQL pattern (now a pointer to `sql-functions`); BI parsing beyond extraction pointers | SDK output contracts win in an SDK run |
| ontology-deep-eda | `data-sampling`, `databricks-sql`, `data-quality-rca` (not used) | none removed: sampling thresholds and system-table patterns are SDK reporting rules; general syntax deferred | SDK output contracts (profiles, `## Joins`) win in an SDK run |

Descriptions now say "Load only in an SDK run project (sdk_config.json at the project root)" and name the stage, so general requests do not trigger them.

## Decisions and assumptions

* Obs 4 marker is a `## Values from EDA` section containing `values_from_eda: true`, not a front matter key: `pages.write_terms` rejects keys outside the `Term` contract and `parse_term_file` ignores unknown front matter. Verified round trip: `write_terms` + `parse_glossary` keep it in `extra_sections`. A front matter field would need a `pages.py` change (request to owner, normal).
* Pattern H uses `spark.sql("DESCRIBE HISTORY ...")` filtered in PySpark because `DESCRIBE HISTORY` cannot be a subquery.

## Checks

* Front matter `name` equals folder; description names the SDK and its stage; YAML parses (first run caught a `: ` in the context-extraction description, fixed): pass.
* `grep PYTHONPATH|sys.path|_vendored` on the three skills: no matches (pass).
* `write_terms` / `parse_glossary` round trip with `Values from EDA` extra section and `Proxy:` line (from a /tmp copy of `src`): pass.
* Word-boundary regex: matches `samples.tpch.part`, not `samples.tpch.partsupp`: pass.
* Balanced code fences in all three files: pass.
* No tests cover skills (`tests/` has no SKILL.md test); bundle validate not applicable (no YAML).

## Requests

* To 26: add the overlap table above to `skills/README.md`.
* To owner: optionally add `values_from_eda` as a `Term` field in `pages.py` if a front matter key is preferred over the section.
