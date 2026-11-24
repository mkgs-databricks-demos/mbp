# Session 05a: Discovery Skills (Research, Context, EDA)

## Scope
Write three Genie Code skills that a pipeline-run session loads: `skills/ontology-domain-research/`, `skills/ontology-context-extraction/`, `skills/ontology-deep-eda/`. Each skill has a `SKILL.md` plus any small reference files it needs.

## Context
* Sources: [L200-B](../../design/L200-B-domain-research.md), [L200-C](../../design/L200-C-supplemental-context.md), [L200-D](../../design/L200-D-deep-eda.md), and the reference plans [l300-pipeline/02](../../design/l300-pipeline/02_domain_research.md), [03](../../design/l300-pipeline/03_supplemental_context.md), [04](../../design/l300-pipeline/04_deep_eda.md).
* Follow the `skill-authoring` skill for the SKILL.md format: YAML front matter `name` + `description` (when to load), then concise instructions, guardrails, and output contract.
* Output locations are relative to the run's project root and must match the run layout in [INDEX.md](../INDEX.md#cross-session-contracts): `docs/research/`, `docs/semantics/` (glossary contract), `docs/context/`, `docs/data_profiles/<table>.md`, `docs/data_profiles/data_model_summary.md`.
* Unattended-session constraints: no Git, no file deletion, read-only SQL, at most 10 web searches, every claim cited with a URL.

## Tasks
1. `ontology-domain-research/SKILL.md`:
   * search strategy: terminology, KPIs, regulatory context, industry benchmarks
   * a research doc template
   * glossary-candidate file format (front matter per INDEX contract)
   * `05_domain_subdomain_proposal.md` template
   * stop rules
2. `ontology-context-extraction/SKILL.md`:
   * reading volume dirs (md, pdf via `ai_parse_document`, docx, csv)
   * PowerBI/Tableau export hints
   * extracting business rules / KPI formulas / join criteria into `docs/context/*.md`
   * extra glossary candidates go to `docs/context/glossary_candidates/` (not `docs/semantics/`, to keep ownership disjoint from research)
   * a clean "no supplemental inputs" path
3. `ontology-deep-eda/SKILL.md`:
   * the L200-D per-table analysis checklist with concrete SQL patterns (null rate, distinct, grain test, FK overlap, cardinality verification query)
   * sampling rules for tables > 10M rows (`TABLESAMPLE`, approx_count_distinct)
   * system-table lineage/usage queries with a fallback when access is denied
   * materialization signals
   * the profile template
   * `data_model_summary.md` template, including a join table with `verified_cardinality` (consumed by mv_yaml rule MV005)
4. Each skill ends with an "Output checklist" the session runner can verify.

## Acceptance Criteria
- [ ] Three `SKILL.md` files exist, each with front matter `name` (matching the folder) and a `description` under 500 characters.
- [ ] Every output path in the skills matches the run layout in INDEX.md (grep check).
- [ ] The EDA skill includes a runnable cardinality verification SQL pattern and a sampling rule.
- [ ] No workspace-specific identifiers.

## Owned Paths / Assets
- `skills/ontology-domain-research/**`
- `skills/ontology-context-extraction/**`
- `skills/ontology-deep-eda/**`

## Dependencies
- Session 01: `docs/design/sdk-layout.md` (skills location).
