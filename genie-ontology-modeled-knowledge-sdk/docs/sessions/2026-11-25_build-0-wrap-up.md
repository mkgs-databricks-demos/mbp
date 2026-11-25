# Build-0 wrap-up

Date: 2026-11-25 | Branch: `mg-genie-ontology-modeled-knowledge-sdk` | Manifest: [docs/plans/waves.json](../plans/waves.json)

The build-level record for build-0. Per-wave detail is in the `w0-*` session summaries; run, repair and job ids are in [2026-11-24_build-waves-instance-deploy.md](2026-11-24_build-waves-instance-deploy.md).

## Verdict

**Build-0 passed.** All 11 waves (`0-0`..`0-10`, 19 sessions, `hybrid` workflow) passed their gates. genie-build-waves has no cross-run verdict yet (framework backlog item 12), so this summary is the build-level verdict.

* Executor: an external monitor (Devin) at level 4; 3 of its 8 allowed repairs used.
* It took three build runs. The last one, a fresh run from `w0-8_sync`, passed waves 0-8, 0-9 and 0-10 (commits `8ace27c`, `d6cce7d`, `cfbb4d0`) with verdict `BUILD_PASSED` at 08:24 UTC.

## Outcome

| Deliverable | Result |
|---|---|
| Library (`config`, `mv_yaml`, `manifest`, `geniespace`, `pages`, `benchmark`, `scaffold`) | done; 280 tests pass after the review fixes |
| Six `skills/ontology-*` | done |
| Bundle templates (`ontology-metric-views`, `ontology-genie-agents`) | done; both pass `bundle validate --strict` |
| Run kit (`templates/run/`) and init notebook | done; the run kit itself was not dogfooded (build-1 R3, R9) |
| TPC-H dogfood (`examples/tpch/`) | 23 glossary terms, 8 profiles, 7 metric views registered (smoke + cardinality pass), 1 Genie Agent (3/3 probes), 93.3% baseline benchmark (14/15), no tuning iteration needed |
| UC Pages | dry run only: no Discover domain for TPC-H (owner deferral) |
| Observations | [docs/build-0-observations.md](../build-0-observations.md): 31 rows from sessions 10a-16 |

## Owner decisions and fixes during the build

| Wave | What happened | Decision |
|---|---|---|
| 0-6 | Metric view registration needed a job-run approval | `jobs.run_now` and `bundle.deploy` approvals granted for the deploying sessions |
| 0-7 | Session 13 (UC Pages) blocked: no Discover domain, and same-titled pages in other domains | Publishing deferred to build 1 (R3 item 3); status set to pass by the owner |
| 0-8 | Agents bundle overrides `schema` did not match the dev metric view schema | Owner fixed the gitignored overrides file; fresh run from `w0-8_sync` (a repair would have kept the SUCCESS iteration) |

## After the build

* **Review:** an SDK code review ([docs/reviews/2026-11-25_build-0-sdk-review.md](../reviews/2026-11-25_build-0-sdk-review.md)) led to build-1 requests R1-R9 ([REQUESTS.md](../plans/build-1/REQUESTS.md)), which the owner accepted.
* **Fixes:** Devin's read-only review of `cfbb4d0` found 1 medium and 4 low findings. All are fixed on the build branch (`71e9711`, plus `5c62bf0` for the mbp root README).
* **Framework:** four genie-build-waves changes came out of this build: PRs #14 (monitor owner fixes, goal over mechanism), #15 (setup pulls the manifest branch, deploy-approval warnings) and #16 (draft Slack escalation), and backlog items 12 and 13 on their own branch.
* **Rename:** the project was renamed to genie-ontology-modeled-knowledge-sdk before merge ([2026-11-25_rename-to-modeled-knowledge-sdk.md](2026-11-25_rename-to-modeled-knowledge-sdk.md)).

## Open items (carry into build 1)

1. Owner reviews and merges the build-0 PR.
2. Point the genie-build-waves instance (vars file, `build_root`, `manifest_path`) at the renamed folder, then redeploy and rerun setup.
3. Create or choose a TPC-H Discover domain and publish the glossary (owner cell in `examples/tpch/docs/pages/pages_registration.md`).
4. Delete the unreferenced `examples/tpch/ontology-genie-agents/agents/ontology_agent.geniespace.json` placeholder.
5. Plan build 1 from R1-R9 merged with the build-0 observations.
