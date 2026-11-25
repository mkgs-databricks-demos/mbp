# Session 24: Discovery Skills — Reconcile & Close Gaps (R8)

## Scope
Reconcile `ontology-domain-research`, `ontology-context-extraction` and `ontology-deep-eda` with platform skills, and fix build-0 observations 1-15.

## Context
* [REQUESTS R8](REQUESTS.md#r8-reconcile-overlapping-skills): SDK skills keep only SDK-specific rules and reference platform skills for general syntax; descriptions trigger only for Genie Ontology Modeled Knowledge SDK work (name the stage and the project files).
* R2 wording: replace any `PYTHONPATH=...vendored` form with the installed package (`gos-*` commands or `python -m genie_ontology_modeled_knowledge_sdk...`).
* Observations ([build-0-observations.md](../../build-0-observations.md)): 1-8 domain research, 9-15 deep EDA. Session 20 adds `pages.write_terms` (obs 8).

## Tasks
1. `ontology-domain-research`:
   * obs 1: dimension tables may carry a `shared` marker (no single subdomain), with a tie-break rule for the rest;
   * obs 2: terms follow business meaning; record the source table separately;
   * obs 3: add `## Sources` to the 05 domain/subdomain proposal template;
   * obs 4: coded column values are deferred to EDA (term field `values_from_eda: true`);
   * obs 5: `proxy` convention in `02_kpi_definitions` and the glossary `Data usage` section;
   * obs 6: one schema-scoped `information_schema.columns` query is the default metadata read;
   * obs 7: cite the current spec version, plus an older one only when it holds the referenced text;
   * obs 8: write term files in bulk with `pages.write_terms`.
2. `ontology-deep-eda`:
   * obs 9: word-boundary regex for usage lookups (`rlike '<schema>\\.<table>([^a-z0-9_]|$)'`);
   * obs 10: lineage counts only, never names;
   * obs 11: pattern D2, unreferenced right keys (`LEFT ANTI JOIN`);
   * obs 12: skip filter/join-column extraction when the usage sample is not diverse (fewer than 5 distinct query shapes), and say so;
   * obs 13: `hot_table` = top `ceil(n / 4)` tables;
   * obs 14: sensitive-column rule (name patterns + free-text columns), values withheld by default;
   * obs 15: ignore maintenance operations (`VACUUM`, `OPTIMIZE`, ...) when deriving update cadence.
3. `ontology-context-extraction`: reconcile only (descriptions, platform references, package wording).
4. For each of the three skills, list in the summary which platform skills overlap and what text was removed; session 26 writes `skills/README.md` from those notes (send them as a request to 26 if 26 has not run yet: same wave, so put them in your summary).

## Acceptance Criteria
- [ ] Gate check `skills_reconciled` passes for these three skills; `no_vendored_paths` finds nothing in them.
- [ ] Each of observations 1-15 is cited in the summary with the file and section that closes it.

## Owned Paths
- `skills/ontology-domain-research/**`, `skills/ontology-context-extraction/**`, `skills/ontology-deep-eda/**`

## Dependencies
- Session 20 (`pages.write_terms`).
