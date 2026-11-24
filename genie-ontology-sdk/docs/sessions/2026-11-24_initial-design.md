# 2026-11-24 — Initial Design

## Goal
Design the Genie Ontology SDK — a developer toolkit that automates the end-to-end standup of modeled knowledge for Genie Ontology.

## Changes
- Created L100 design document (canvas)
- Resolved all 7 open design questions
- Created mbp section with full file structure:
  - README with Documents, Research, Semantics, Diagrams, Examples tables
  - 3 research documents (MV CI/CD, Agent API, Semantic Metadata)
  - 1 semantics document (SDK Glossary)
  - 5 Mermaid diagrams (Architecture, Waves Sequence, Two-DAB, forEach, CI/CD)
  - 2 example DAB bundles (DAB 1 metric views, DAB 2 agents)
  - 1 example metric view YAML with materialization
  - 1 example .geniespace.json
  - Session log and index

## Decisions

| # | Question | Decision |
|---|---|---|
| 1 | Pages deployment | Include — full automation (Wave 5.5) |
| 2 | Domain/Subdomain registration | Hybrid — generate proposal, opt-in creation |
| 3 | Materialization | Include — auto-generate materialization blocks |
| 4 | SGT App integration | Defer — separate products |
| 5 | Genie Observability | Defer — wait for native Genie Agent tracing |
| 6 | Incremental re-runs | Full regeneration (idempotent) |
| 7 | Multi-workspace deployment | Single workspace v1 |

## Verification
- All files written to `/Workspace/Users/matthew.giglia@databricks.com/mbp/genie-ontology-sdk/`
- Follows mbp conventions: README with tables, docs/, examples/, docs/sessions/

## Observations
- The forEach task pattern for MV registration is well-proven in genie-build-waves
- Native DAB `genie_spaces` resource with `file_path` is cleaner than REST API calls
- Materialization auto-detection is a differentiator — most manual standups skip this
- The 50 MV threshold for agent splitting needs empirical validation across domains

## Follow-ups
- [x] Write L200-A through L200-H design documents
- [x] Build example notebooks (generate_manifest.py, register_single_mv.py)
- [x] Create the Genie Build Waves manifest (waves.json) for the SDK pipeline
- [x] Render Mermaid diagrams to SVG/HTML (mermaid-py via mermaid.ink API)
- [x] Add to root README topic table
- [ ] Create feature branch mg-genie-ontology-sdk
- [ ] Push to GitHub
