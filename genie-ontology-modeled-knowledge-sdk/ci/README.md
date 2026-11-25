# CI for the Genie Ontology Modeled Knowledge SDK (staged)

Build sessions write only inside the SDK folder, so repository-root CI files are **staged here** and moved by the owner.

## Files

| Staged file | Moves to (repository root) | What it does |
|---|---|---|
| `ci/github/workflows/genie-ontology-modeled-knowledge-sdk-ci.yml` | `.github/workflows/genie-ontology-modeled-knowledge-sdk-ci.yml` | Runs on pull requests that touch `genie-ontology-modeled-knowledge-sdk/**`. Jobs: `lint` (ruff check + format check), `typecheck` (mypy), `test` (pytest, matrix: the `databricks-sdk` floor and the latest release; `GENIE_BUILD_WAVES_DIR` points at the repo's `genie-build-waves/`), `bundle-validate` (`databricks bundle validate --strict` on the SDK bundle's three targets and both templates, with GitHub OIDC; skipped until the OIDC variables are set) |

The wheel build step is added in build 1 by session 23.

## Local equivalents

Run from the SDK folder (a copy outside `/Workspace` if pytest hits workspace file system limits):

```bash
pip install -e ".[dev]"
ruff check . && ruff format --check .
mypy src
GENIE_BUILD_WAVES_DIR=../genie-build-waves python -m pytest -q -rs
```

Lint scope is `src/` and `tests/` (see `[tool.ruff] extend-exclude` in `pyproject.toml`). Notebooks, templates, examples and skills are excluded until their owners bring them under lint.

## databricks-sdk floor

`pyproject.toml` pins `databricks-sdk>=0.45.0,<1`. The floor is the first release that has every `WorkspaceClient` method the SDK calls; `tests/test_sdk_services.py` checks them, and the CI `test` matrix runs it on the floor and the latest release. Keep the floor, the matrix entry and this table in sync.

Evidence: each release below was installed and the attributes probed on a `WorkspaceClient` (no network calls). 0.40.0 was the earliest release probed, so "<= 0.40.0" means present in every probed release.

| API used | Where | First probed release with it |
|---|---|---|
| `w.genie.start_conversation_and_wait` | `benchmark` | <= 0.40.0 |
| `w.genie.get_message_attachment_query_result` | `benchmark` | **0.45.0** (missing in 0.44.0) - sets the floor |
| `w.statement_execution.execute_statement` | `benchmark` | <= 0.40.0 |
| `w.catalogs.get`, `w.schemas.get`, `w.schemas.list`, `w.tables.get`, `w.tables.list` | `config` | <= 0.40.0 |
| `w.files.list_directory_contents` | `config` | <= 0.40.0 |
| `w.api_client.do` | `pages` (UC Pages REST), Genie eval-runs and skills APIs with no SDK wrapper | <= 0.40.0 (no floor needed) |

Upper bound: `<1` (next major).

## Owner setup (P1-7)

1. Move the workflow file to `.github/workflows/` at the repository root.
2. Create a service principal for CI in the dev workspace and a GitHub OIDC federation policy for this repository (no stored secret).
3. Set repository variables `DATABRICKS_HOST` and `DATABRICKS_CLIENT_ID` (the service principal's application id). `bundle-validate` runs only when both are set.
4. Grant the service principal what `bundle validate` needs (workspace access and `USE CATALOG` on the catalogs the placeholder overrides name, if any).
5. Branch protection on `main`: require the `lint`, `typecheck` and `test` checks (and `bundle-validate` once OIDC is configured).
