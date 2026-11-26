# Session 02: Domain Research & Glossary

## Scope
Research the `bakehouse_retail_sales` domain on the public web and write cited research documents plus glossary term files. This session runs in parallel with sessions 03 and 04.

## Context
* Skill: load `skills/ontology-domain-research/SKILL.md` (shipped with the SDK) and follow its search budget, stop rules and output contracts.
* Inputs: `sdk_config.json` (`domain_name`, `domain_context`, source tables), `docs/inputs_report.md` (expanded table list). Read table metadata only; no data scans.
* Glossary term contract (`docs/semantics/<term>.md`): front matter `term`, `synonyms`, `domain`, `subdomain`, `related_terms`, `sources`; body sections Definition, Business context, Data usage. Check parsing with `genie_ontology_modeled_knowledge_sdk.pages.parse_glossary('docs/semantics')`.
* Do not write `docs/context/**` (session 03) or `docs/data_profiles/**` (session 04).

## Tasks
1. Plan the searches per the skill (at most 10).
2. Write `docs/research/01_terminology.md`, `02_kpi_definitions.md` (formulas: numerator, denominator, grain, period), `03_regulatory_context.md`, `04_benchmarks.md`, and `05_domain_subdomain_proposal.md` (proposed subdomains, which source tables and KPIs belong to each).
3. Write one glossary term file per core term and KPI in `docs/semantics/`.
4. Run `parse_glossary` on `docs/semantics/` and fix every file it rejects.

## Acceptance Criteria
- [ ] Research docs 01-05 exist and each cites at least one URL.
- [ ] `parse_glossary('docs/semantics')` parses every term file.
- [ ] No workspace-specific identifiers in any file.

## Owned Paths
- `docs/research/**`
- `docs/semantics/**`

## Dependencies
- Session 01: `docs/inputs_report.md`.
