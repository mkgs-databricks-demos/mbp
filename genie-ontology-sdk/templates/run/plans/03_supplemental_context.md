# Session 03: Supplemental Context Extraction

## Scope
Extract business rules, KPI formulas, join criteria, filters and hierarchies from the owner's supplemental files for `{{domain_name}}` into `docs/context/`. This session runs in parallel with sessions 02 and 04.

## Context
* Skill: load `skills/ontology-context-extraction/SKILL.md` and follow its inventory, extraction, budget and no-inputs rules.
* Inputs: `sdk_config.json` (`supplemental_volume_dirs`, `dashboard_inputs`), `docs/inputs_report.md` (`## Supplemental inputs`). Volume files are read-only.
* Session 02 writes `docs/research/05_domain_subdomain_proposal.md` in parallel. If it is not there yet, tag findings `subdomain: unassigned`.
* Glossary candidates go to `docs/context/glossary_candidates/` (same front matter contract as `docs/semantics/`), never to `docs/semantics/`. The UC Pages session merges both.

## Tasks
1. Inventory every supplemental file into `docs/context/00_source_inventory.md`. With no inputs, write only that file with `## Status: no supplemental inputs provided`.
2. Extract business rules, KPI formulas, join criteria and dimensions/filters into `docs/context/*.md`, citing the source file for each item.
3. Write glossary candidates for terms that the files define.

## Acceptance Criteria
- [ ] `docs/context/00_source_inventory.md` exists.
- [ ] Every extracted item cites its `/Volumes/...` source.
- [ ] Unreadable paths are listed with their error. All paths unreadable means `status: "blocked"`.

## Owned Paths
- `docs/context/**`

## Dependencies
- Session 01: `docs/inputs_report.md`.
