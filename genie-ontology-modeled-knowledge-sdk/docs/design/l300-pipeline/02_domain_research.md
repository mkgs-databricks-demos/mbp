# Session 02 — Domain Research — Industry & Terminology

**Wave:** 1 — Domain Research
**Mode:** execute
**Depends on:** 01
**Estimated effort:** Medium (~30 min)

## Goal

Research the domain described in `domain_context` using web search. Capture industry-standard terminology, KPIs, regulatory context, benchmarks, and propose a UC domain/subdomain structure.

## Context

Read `sdk_config.json` for the `domain_context` string and `all_tables` list. Table and column names provide additional domain signals.

## Tasks

### 1. Domain Overview Research

Search for: industry definition, scope, key stakeholders, competitive landscape, standard data models.

Write to: `docs/research/01_domain_overview.md`

### 2. KPI Definitions

Search for: standard KPIs with formulas, calculation methods (numerator, denominator, grain, time period), industry benchmarks (median, top quartile).

Write to: `docs/research/02_kpi_definitions.md`

### 3. Regulatory Context

Search for: applicable regulations, required reporting metrics, compliance standards, data privacy requirements.

Write to: `docs/research/03_regulatory_context.md`

### 4. Industry Benchmarks

Search for: quantitative benchmarks, performance tiers, trend data.

Write to: `docs/research/04_industry_benchmarks.md`

### 5. Domain/Subdomain Proposal

Based on all research, propose UC Domain name, Subdomain names, which tables/MVs belong to each, and rationale.

Write to: `docs/research/05_domain_subdomain_proposal.md`

### 6. Glossary Candidates

For every domain-specific term, create a glossary entry in `docs/semantics/` following the UC Pages format: Definition, Business Context, Data Usage, Related Terms, Source.

Organize by subdomain (one file per subdomain cluster).

## Pass Criteria

- [ ] At least 5 research documents in `docs/research/`
- [ ] Domain/subdomain proposal with rationale
- [ ] At least 10 glossary candidates in `docs/semantics/`
- [ ] All documents include Sources section with citations
- [ ] Quantitative data captured (market size, benchmarks, dollar impacts)
