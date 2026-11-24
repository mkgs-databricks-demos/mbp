# Session 09: Genie Agent Deployment & Probe

## Scope
Render and deploy the `ontology-genie-agents` bundle to the `dev` target, ask each deployed agent one sample question, and record the space ids and results in `docs/deployment/`. This is the only session in its wave, because it deploys.

## Context
* Skill: none required. `ontology-genie-agents/README.md` documents the render step, the overrides file and deploy (`genie_spaces` resource, `engine: direct`).
* Workspace values come from the gitignored `ontology-genie-agents/.databricks/bundle/dev/variable-overrides.json`, written by the owner. Never print, edit or commit it. If it is missing, stop with `status: "blocked"`.
* Approvals: `bundle.deploy` of this bundle is implied by `allow_deploy`. Asking a question through the Genie conversation API is a read of the deployed agent.
* Do not edit agent files here. A defect in an agent file is session 08's: record a `request` and stop with `status: "fail"`.

## Tasks
1. From `ontology-genie-agents/`, run the render step (if any), `bundle validate --strict --target dev`, then `bundle deploy --target dev`.
2. Read each deployed space id from `bundle summary`.
3. For each agent, run `w.genie.start_conversation_and_wait(space_id, <first sample question>)`. Check that it returns a query attachment and that `get_message_attachment_query_result` is `SUCCEEDED`.
4. Write `docs/deployment/deployment_results.md` with one row per agent: resource key, space id, deploy time, probe question, attachment type, query state, error.

## Acceptance Criteria
- [ ] Every agent is deployed after this build run started, and its space id is recorded (also under `resolved_targets` in the status file).
- [ ] Every probe returned a `SUCCEEDED` query attachment. A text-only answer is a failure: record it for session 10.

## Owned Paths
- `docs/deployment/**`

## Dependencies
- Session 08: agent files and resource entries.
