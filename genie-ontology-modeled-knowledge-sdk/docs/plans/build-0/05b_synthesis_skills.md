# Session 05b: Synthesis Skills (MV Synthesis, Agent Curation, Tuning)

## Scope
Write three Genie Code skills: `skills/ontology-mv-synthesis/`, `skills/ontology-agent-curation/`, `skills/ontology-tuning/`. Each has a `SKILL.md` plus small reference files.

## Context
* Sources: [L200-E](../../design/L200-E-metric-view-synthesizer.md), [L200-G](../../design/L200-G-genie-agent-curator.md), [L200-H](../../design/L200-H-tuning-engine.md); reference plans [l300-pipeline/05](../../design/l300-pipeline/05_metric_view_synthesis.md), [08](../../design/l300-pipeline/08_genie_agent_curation.md), [10](../../design/l300-pipeline/10_tuning_engine.md).
* The skills call the SDK library built in wave 0-1 by its contract names (INDEX.md): `genie_ontology_modeled_knowledge_sdk.mv_yaml`, `manifest`, `geniespace`, `benchmark`. Refer to function names only; sessions 02-04 own the code.
* Follow the `skill-authoring` format. The existing `metric-views` platform skill covers YAML syntax; reference it instead of restating the spec.
* Core principle: tune metric views (comments, synonyms, display names, measures) before agent instructions; agent instructions only for genuinely ambiguous terms.

## Tasks
1. `ontology-mv-synthesis/SKILL.md`:
   * inputs (research, context, data profiles)
   * one MV per business process/grain
   * parameter tokens
   * explicit fields
   * joins only with `verified_cardinality` from EDA
   * semantic metadata from research synonyms
   * materialization thresholds (row count, join count, KPI frequency), with only categorical dimensions
   * file layout `ontology-metric-views/metric_views/<domain>/*.yml`
   * finish with `python -m genie_ontology_modeled_knowledge_sdk.mv_yaml validate` + `manifest.write_manifest`
2. `ontology-agent-curation/SKILL.md`:
   * `plan_agents` / `build_space` usage
   * sample questions from research KPIs (5-10)
   * minimal text instructions
   * example SQL only for multi-step questions
   * `domain_manifest.yml` (proposal only; domain creation is opt-in)
   * output `ontology-genie-agents/agents/*.geniespace.json`
3. `ontology-tuning/SKILL.md`:
   * benchmark question generation (10-20 per agent, with expected SQL or answers where derivable)
   * running `benchmark.run_benchmark`
   * failure triage table (missing measure / synonym gap / join issue / ambiguity)
   * a fix-the-MV-first loop with a max of 2 iterations
   * `docs/tuning/tuning_plan.md` and `benchmark_results.md` templates
   * the accuracy definition quoted from `benchmark.py`
4. Each skill ends with an "Output checklist".

## Acceptance Criteria
- [ ] Three `SKILL.md` files exist with valid front matter (`name` = folder name).
- [ ] Every SDK function a skill names exists in the INDEX.md contract table (grep check).
- [ ] The tuning skill states the MV-first rule and the iteration limit.

## Owned Paths / Assets
- `skills/ontology-mv-synthesis/**`
- `skills/ontology-agent-curation/**`
- `skills/ontology-tuning/**`

## Dependencies
- Session 01: layout. Contract names from INDEX.md (sessions 02-04 run in parallel and implement them).
