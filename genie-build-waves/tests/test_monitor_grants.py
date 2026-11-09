"""Tests for monitor_grants.py (least-privilege grants for the external monitor skill)."""

import json
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "notebooks"))

from monitor_grants import (  # noqa: E402
    grant_command,
    held_privileges,
    missing_grants,
    monitor_grant_plan,
    principal_problem,
)

PLAN = monitor_grant_plan("cat", "sch", "genie_build_monitor")


def test_plan_is_traversal_plus_read_on_the_one_skill():
    assert PLAN == [
        ("catalog", "cat", "USE_CATALOG"),
        ("schema", "cat.sch", "USE_SCHEMA"),
        ("skill", "cat.sch.genie_build_monitor", "READ_VOLUME"),
    ]
    # Never READ VOLUME on the schema (would cover every skill and volume in it)
    assert ("schema", "cat.sch", "READ_VOLUME") not in PLAN


def test_held_privileges_reads_dicts_and_sdk_objects_including_groups():
    as_dicts = [
        {"principal": "account users", "privileges": [{"privilege": "READ_METADATA", "inherited_from_name": "metastore"}]},
        {"principal": "monitor-group", "privileges": [{"privilege": "USE_CATALOG"}]},
    ]
    assert held_privileges(as_dicts) == {"READ_METADATA", "USE_CATALOG"}
    enum_like = SimpleNamespace(value="USE_SCHEMA")
    as_objects = [SimpleNamespace(principal="spn", privileges=[SimpleNamespace(privilege=enum_like)])]
    assert held_privileges(as_objects) == {"USE_SCHEMA"}
    assert held_privileges(None) == set()


def test_missing_grants_skips_held_and_all_privileges():
    held = {
        ("catalog", "cat"): {"USE_CATALOG"},
        ("schema", "cat.sch"): {"ALL_PRIVILEGES"},
    }
    assert missing_grants(PLAN, held) == [("skill", "cat.sch.genie_build_monitor", "READ_VOLUME")]
    assert missing_grants(PLAN, {}) == PLAN
    # READ_METADATA (granted to account users on the metastore) does not count as READ_VOLUME
    assert missing_grants(PLAN[2:], {PLAN[2][:2]: {"READ_METADATA"}}) == PLAN[2:]


def test_principal_problem():
    assert principal_problem("00000000-0000-4000-8000-000000000000") == ""
    assert principal_problem("monitor-agents") == ""
    assert principal_problem("someone@example.com") == ""
    assert "empty" in principal_problem("")
    assert "whitespace" in principal_problem(" abc")
    assert "placeholder" in principal_problem("<application id>")
    assert "placeholder" in principal_problem("${var.monitor_principal}")


def test_grant_command_is_valid_cli_json():
    cmd = grant_command("skill", "cat.sch.genie_build_monitor", "READ_VOLUME", "abc")
    assert cmd.startswith("databricks grants update skill cat.sch.genie_build_monitor --json '")
    body = json.loads(cmd.split("--json '", 1)[1].rstrip("'"))
    assert body == {"changes": [{"principal": "abc", "add": ["READ_VOLUME"]}]}
