# Session 08 — Genie Agent Curation & Configuration

**Wave:** 6 — Genie Agent Curation
**Mode:** edit
**Depends on:** 06, 07
**Estimated effort:** Heavy (~30 min, may need continuation)

## Goal

Determine agent organization, generate `.geniespace.json` configuration files, and create the domain manifest.

## Context

Read: `sdk_config.json` (max_metric_views_per_agent, domain_name), `ontology-metric-views/metric_views/manifest.json`, `docs/research/05_domain_subdomain_proposal.md`, `docs/research/02_kpi_definitions.md`, `docs/context/*.md`, `docs/data_profiles/data_model_summary.md`, `examples/agents/sales_agent.geniespace.json` (reference).

## Tasks

### 1. Determine Agent Organization

Count total MVs. If <= max_metric_views_per_agent: single agent. If >: split by subdomain, minimizing redundancy and ambiguity, maximizing usability.

### 2. Generate .geniespace.json

For each agent:
- **data_sources.tables** — registered metric views
- **instructions.text_instructions** — ONLY genuinely ambiguous terms and business rules not in MV metadata. Do NOT duplicate MV comments/synonyms.
- **instructions.example_question_sqls** — ONLY complex multi-step queries. Use MEASURE() syntax. Do NOT add examples for straightforward queries.
- **instructions.join_specs** — verified join relationships
- **config.sample_questions** — 3-5 business-relevant questions

All IDs: lowercase 32-char hex, no hyphens, stable (derive from content hash).

### 3. Generate Domain Manifest

Write `docs/domain_manifest.yml` with domains, subdomains, metric_views, agents, pages.

## Pass Criteria

- [ ] At least one .geniespace.json
- [ ] Agent organization follows threshold rule
- [ ] Each agent references only registered MVs
- [ ] Instructions are minimal (no overfitting)
- [ ] domain_manifest.yml exists
- [ ] All IDs are valid 32-char hex
