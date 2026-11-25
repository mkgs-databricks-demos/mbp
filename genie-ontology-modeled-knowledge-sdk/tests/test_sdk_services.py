"""The databricks-sdk floor: every WorkspaceClient service and method the SDK calls exists.

CI runs this against the floor in pyproject.toml and the latest release, so a
too-low floor or a removed method fails here (see ci/README.md for the table).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "ci" / "github" / "workflows" / "genie-ontology-modeled-knowledge-sdk-ci.yml"

# (service, method) pairs called by src/genie_ontology_modeled_knowledge_sdk.
USED = [
    ("genie", "start_conversation_and_wait"),  # benchmark
    ("genie", "get_message_attachment_query_result"),  # benchmark; sets the floor (0.45.0)
    ("statement_execution", "execute_statement"),  # benchmark
    ("catalogs", "get"),  # config.check_access
    ("schemas", "get"),  # config.check_access
    ("schemas", "list"),  # config.expand_tables
    ("tables", "get"),  # config.check_access
    ("tables", "list"),  # config.expand_tables
    ("files", "list_directory_contents"),  # config.check_access
    ("api_client", "do"),  # pages.RestPagesClient (and raw REST calls with no SDK wrapper)
]


def _floor() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'"databricks-sdk>=([0-9.]+),<([0-9]+)"', text)
    assert m, "pyproject.toml must pin databricks-sdk>=<floor>,<next major>"
    return m.group(1)


def _version(v: str) -> tuple[int, ...]:
    return tuple(int(p) for p in re.findall(r"\d+", v)[:3])


@pytest.fixture(scope="module")
def ws():
    sdk = pytest.importorskip("databricks.sdk")
    # Token auth with a dummy host: building the client makes no network call.
    return sdk.WorkspaceClient(host="https://example.cloud.databricks.com", token="dummy")


def test_installed_sdk_meets_floor():
    version = pytest.importorskip("databricks.sdk.version").__version__
    assert _version(version) >= _version(_floor()), f"databricks-sdk {version} is below the floor {_floor()}"


@pytest.mark.parametrize(("service", "method"), USED, ids=[f"{s}.{m}" for s, m in USED])
def test_workspace_client_has_method(ws, service, method):
    svc = getattr(ws, service, None)
    assert svc is not None, f"WorkspaceClient has no {service!r} service"
    assert callable(getattr(svc, method, None)), f"WorkspaceClient.{service} has no {method!r}"


def test_ci_matrix_tests_the_floor():
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    matrix = workflow["jobs"]["test"]["strategy"]["matrix"]["databricks-sdk"]
    assert _floor() in matrix and "latest" in matrix
