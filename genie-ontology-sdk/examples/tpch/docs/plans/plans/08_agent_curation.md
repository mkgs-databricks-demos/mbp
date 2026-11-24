# Session 08: Genie Agent Curation

## Scope
Organize the registered `tpch_supply_chain` metric views into Genie Agents. Use one agent unless the views exceed `max_metric_views_per_agent`; otherwise split by subdomain. Write tokenized `.geniespace.json` files, one `genie_spaces` resource entry per agent, and `docs/domain_manifest.yml`. This session writes files only; deployment is session 09.

## Context
* Skill: load `skills/ontology-agent-curation/SKILL.md` and follow its MV-first, minimal-instruction rules.
* SDK functions (`genie_ontology_sdk.geniespace`): `plan_agents(mvs, max_per_agent=50)`, `build_space(plan, ...)`, `validate_space(doc)`, `write_domain_manifest(plans, path)`, and the render CLI `python -m genie_ontology_sdk.geniespace render <src> <dst> --params <json>`.
* Inputs: `ontology-metric-views/metric_views/manifest.json`, `docs/registration/registration_results.md` (curate registered views only), `docs/research/**`, `docs/context/**`, `docs/data_profiles/data_model_summary.md`, and the `ontology-genie-agents/README.md` resource pattern.
* Committed agent files stay tokenized (`${target_catalog}.${target_schema}.<view>`). Never write a resolved catalog, schema or warehouse id.
* No deploys, and no Genie API writes.

## Tasks
1. Build the metric view list from the manifest, keeping only registered views, and call `plan_agents`.
2. For each plan, run `build_space` and write `ontology-genie-agents/agents/<agent>.geniespace.json`. Each file must pass `validate_space`.
3. Add one `genie_spaces` resource entry per agent under `ontology-genie-agents/resources/`, following the template's existing entry. Remove the template placeholder agent once real agents replace it.
4. Run `write_domain_manifest(plans, 'docs/domain_manifest.yml')`.
5. From `ontology-genie-agents/`, run the README's render step (if any), then `bundle validate --strict --target dev`. Validate only; do not deploy.

## Acceptance Criteria
- [ ] Every agent file passes `validate_space` and references at most `max_metric_views_per_agent` registered views.
- [ ] Agent files contain no literal catalog, schema or warehouse id.
- [ ] `bundle validate --strict` passes for the agents bundle.
- [ ] `docs/domain_manifest.yml` exists.

## Owned Paths
- `ontology-genie-agents/agents/**`
- `ontology-genie-agents/resources/**`
- `docs/domain_manifest.yml`

## Dependencies
- Session 05: `manifest.json`. Session 06: registration results.
