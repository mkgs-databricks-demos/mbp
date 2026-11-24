# Session 07 — UC Pages Registration

**Wave:** 5.5 — UC Pages Registration
**Mode:** execute
**Depends on:** 06
**Estimated effort:** Light (~15 min)

## Goal

Register UC Pages from the glossary candidates generated in Waves 1-2.

## Context

Read `docs/semantics/*.md` for glossary candidates. Read `docs/research/05_domain_subdomain_proposal.md` for domain associations.

## Tasks

### 1. Parse Glossary Candidates

Read all files in `docs/semantics/`. Extract each term entry (delimited by `## Term Name`).

### 2. Register UC Pages

For each glossary term, create a UC Page using the workspace client or REST API. Each page includes: definition, business context, data usage, related terms, source.

### 3. Associate with Domains

If domains/subdomains exist, associate each Page with its domain.

### 4. Record Results

Write to `docs/tuning/pages_registration_results.md`: list of registered Pages, domain associations, any failures.

## Pass Criteria

- [ ] All glossary candidates registered as UC Pages
- [ ] Pages associated with domains (if domains exist)
- [ ] Results documented
