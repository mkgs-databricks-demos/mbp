# Genie Ontology SDK — Session Plan Index

**Project:** Genie Ontology SDK
**Created:** 2026-11-24
**Workflow mode:** hybrid

---

## Session Order

| # | Session | Produces | Depends On | Est. Effort |
|---|---------|----------|------------|-------------|
| 01 | [Input Validation & Scaffolding](01_input_validation_scaffolding.md) | sdk_config.json, folder structure, feature branch | Nothing | Light |
| 02 | [Domain Research](02_domain_research.md) | docs/research/*.md, docs/semantics/*.md | 01 | Medium |
| 03 | [Supplemental Context](03_supplemental_context.md) | docs/context/*.md, additional semantics | 01 | Medium |
| 04 | [Deep EDA](04_deep_eda.md) | docs/data_profiles/*.md, data_model_summary.md | 01 | Heavy |
| 05 | [Metric View Synthesis](05_metric_view_synthesis.md) | metric_views/*.yml, manifest.json | 02, 03, 04 | Heavy |
| 06 | [MV Registration](06_metric_view_registration.md) | Registered metric views in UC | 05 | Medium |
| 07 | [Pages Registration](07_pages_registration.md) | Registered UC Pages | 06 | Light |
| 08 | [Agent Curation](08_genie_agent_curation.md) | agents/*.geniespace.json, domain_manifest.yml | 06, 07 | Heavy |
| 09 | [Agent Deployment](09_genie_agent_deployment.md) | Deployed Genie Agents | 08 | Medium |
| 10 | [Tuning](10_tuning_engine.md) | tuning_plan.md, benchmark_results.md, updated YAMLs | 09 | Heavy |

---

## Build Waves

### Wave 0 — Initialization (serial)

| Session | Notes |
|---|---|
| **01 Input Validation & Scaffolding** | Creates working environment. Must pass before any other work. |

**Gate:** Feature branch exists, all inputs accessible, sdk_config.json written.

### Wave 1 — Domain Research (serial)

| Session | Notes |
|---|---|
| **02 Domain Research** | Web search for terminology, KPIs, regulatory context. |

**Gate:** At least 3 research docs, glossary candidates, domain/subdomain proposal.

### Wave 2 — Supplemental Context (serial, parallel with Wave 1 after Wave 0)

| Session | Notes |
|---|---|
| **03 Supplemental Context** | Parse volume files and dashboard inputs. |

**Gate:** Context docs for all supplemental sources, additional glossary candidates.

### Wave 3 — Deep EDA (serial, parallel with Waves 1-2 after Wave 0)

| Session | Notes |
|---|---|
| **04 Deep EDA** | Profile every source table. May need continuation. |

**Gate:** One profile per table, data_model_summary.md, join keys with cardinality.

### Wave 4 — Metric View Synthesis (serial, depends on Waves 1-3)

| Session | Notes |
|---|---|
| **05 MV Synthesis** | Synthesize all context into parameterized YAMLs. May need continuation. |

**Gate:** YAMLs parameterized, joins annotated, materialization blocks, manifest.json valid.

### Wave 5 — Metric View Registration (serial)

| Session | Notes |
|---|---|
| **06 MV Registration** | CREATE OR REPLACE VIEW for each MV. Smoke tests. |

**Gate:** All MVs registered, smoke tests pass, cardinality tests pass.

### Wave 5.5 — UC Pages Registration (serial)

| Session | Notes |
|---|---|
| **07 Pages Registration** | Register glossary candidates as UC Pages. |

**Gate:** All Pages registered, domain associations set.

### Wave 6 — Genie Agent Curation (serial)

| Session | Notes |
|---|---|
| **08 Agent Curation** | Determine organization, generate .geniespace.json. May need continuation. |

**Gate:** At least one agent config, 50 MV threshold respected, domain manifest exists.

### Wave 7 — Genie Agent Deployment (serial)

| Session | Notes |
|---|---|
| **09 Agent Deployment** | Deploy agents, validate accessibility. |

**Gate:** All agents deployed, each responds to sample question.

### Wave 8 — Tuning (serial, multiple continuation passes)

| Session | Notes |
|---|---|
| **10 Tuning** | Benchmark, diagnose, fix MVs first, re-test. |

**Gate:** Tuning plan documented, benchmark accuracy >= 70%.

---

## Dependency Graph

```
Wave 0: [01]
           |
     +-----+-----+
     |     |      |
Wave 1: [02]  Wave 2: [03]  Wave 3: [04]
     |     |      |
     +-----+------+
           |
Wave 4: [05]
           |
Wave 5: [06]
           |
Wave 5.5: [07]
           |
Wave 6: [08]
           |
Wave 7: [09]
           |
Wave 8: [10]
```

Note: Waves 1, 2, and 3 can run in parallel after Wave 0 (they all depend only on session 01). Wave 4 waits for all three to complete.
