# 2026-11-24 — Wave 0-1, Session 05b: Synthesis Skills

Run id: 701596191246320 (job 419885870201924). Branch `mg-genie-ontology-modeled-knowledge-sdk` (checked read-only: on branch, clean tree at start). Mode: `edit`.

## Scope

Plan `build-0/05b`: SKILL.md files for `ontology-mv-synthesis`, `ontology-agent-curation`, `ontology-tuning`. Manifest scope and plan agree.

## Changes

| File | Contents |
|---|---|
| `skills/ontology-mv-synthesis/SKILL.md` | inputs table (research, glossary, context, profiles, data_model_summary); one MV per business process/grain; four parameter tokens; explicit fields; joins only with `verified_cardinality` + `# verified:` comment (MV005); semantic metadata from glossary synonyms; materialization thresholds (>= 10M source rows, >= 3 joins, headline KPI) with `refresh_policy: auto`, `cluster_by: {auto: true}`, categorical dimensions only; layout `ontology-metric-views/metric_views/<domain>/*.yml`; finishes with `python -m genie_ontology_sdk.mv_yaml validate` + `manifest.build_manifest` / `validate_manifest_json` / `write_manifest`; output checklist |
| `skills/ontology-mv-synthesis/references/yaml-patterns.md` | tokenized fact-view example, many-to-many handling, materialization block, validator anti-pattern table |
| `skills/ontology-agent-curation/SKILL.md` | `plan_agents` (50-MV rule) / `build_space` / `validate_space` usage; 5-10 sample questions from research KPIs; minimal text instructions; example SQL only for multi-step questions; join specs only when verified; `geniespace render` check to a scratch folder; `write_domain_manifest` to `docs/domain_manifest.yml` (proposal only, domain creation opt-in); output `ontology-genie-agents/agents/*.geniespace.json`; output checklist |
| `skills/ontology-tuning/SKILL.md` | MV-first rule and 2-iteration limit up front; 10-20 benchmark questions per agent with tags and `expected_sql`/`expected_answer`; `load_questions` / `run_benchmark` / `score` / `write_results_md`; accuracy definition; 70% gate; failure triage table (missing measure / synonym gap / join issue / ambiguity) with MV fix vs agent fix; output checklist |
| `skills/ontology-tuning/references/templates.md` | templates for `docs/tuning/tuning_plan.md`, `benchmark_results.md`, `benchmark_questions.yml` |

## Decisions

* YAML syntax is delegated to the platform `metric-views` skill (`joins-correctness.md`, `materialization.md`, `semantic-metadata.md`), per the plan; the skill only adds SDK rules.
* Join verification is recorded as a `# verified: ...` YAML comment (one of the two MV005 options), not a `verified_cardinality` YAML key, because an unknown key could fail registration.
* The skill warns that a `materialization:` block cannot be combined with a metric view `parameters:` block; the `${...}` registration tokens are not affected.
* Sample questions per agent: 5-10 (plan 05b), overriding the 3-5 in the reference `l300-pipeline/08`.
* Materialization thresholds are SDK defaults; if the EDA profiles state different thresholds, the skill uses theirs.

## Assumptions (parallel sessions in wave 0-1)

* `benchmark.py` (session 04) did not exist yet. The accuracy definition in the tuning skill is taken from plan 04 (`accuracy = matches / questions with expectations, else succeeded / total`); the skill tells the runner to quote the `benchmark.py` docstring verbatim and update the line if it differs.
* `manifest.write_manifest(...)` has no signature in the INDEX contract; the skill tells the runner to check it with `help()`.
* How `manifest.build_manifest` derives `subdomain` is up to session 02; the skill defaults to a leading `# subdomain: <name>` YAML comment unless `help(manifest.build_manifest)` documents another source. Session 02 / 11 should confirm.
* `plan_agents` input items carry `name`, `fq_name`, `domain`, `subdomain` (plan 03).

## Checks

| Check | Result |
|---|---|
| Three SKILL.md files with front matter `name` = folder name | pass (regex search: `name: ontology-mv-synthesis`, `ontology-agent-curation`, `ontology-tuning` at line 2 of each) |
| Every SDK function named exists in the INDEX contract table | pass (manual review: `substitute`, `render_ddl`, `build_manifest`, `write_manifest`, `validate_manifest_json`, `plan_agents`, `build_space`, `validate_space`, `write_domain_manifest`, `render_space_file`, `load_questions`, `run_benchmark`, `score`, `write_results_md`, `scaffold_project`, CLIs `mv_yaml validate` and `geniespace render`). An automated grep was not possible: regex search matches whole files and the session has no execute approval |
| Tuning skill states MV-first rule and iteration limit | pass (section "The MV-first rule") |
| Descriptions under 500 characters | pass (each about 300) |
| pytest / bundle validate | skipped (no code or YAML touched; `allow_execute` not set) |

## Requests

None.
