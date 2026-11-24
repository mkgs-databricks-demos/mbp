# Session 09 — Genie Agent Deployment & Validation

**Wave:** 7 — Genie Agent Deployment
**Mode:** execute
**Depends on:** 08
**Estimated effort:** Medium (~20 min)

## Goal

Deploy all Genie Agents and validate they are accessible and functional.

## Context

Read: `ontology-genie-agents/agents/*.geniespace.json`, `sdk_config.json` (warehouse_id, domain_name).

## Tasks

### 1. Deploy via Genie API

For each .geniespace.json: POST to /api/2.0/genie/spaces with serialized_space as a JSON string, warehouse_id, title, description, parent_path. Record each space_id.

### 2. Validate Each Agent

For each deployed agent: start a conversation via the conversation API with the first sample question. Verify: accessible (no 403/404), responds, includes generated SQL.

### 3. Record Results

Write to `docs/tuning/deployment_results.md`: agent name, space_id, title, MV count, validation status, any errors.

## Pass Criteria

- [ ] All agents deployed successfully
- [ ] Each agent responds to at least one sample question
- [ ] Deployment results documented with space_ids
