"""Tests for genie_ontology_modeled_knowledge_sdk.config (input contract)."""

from __future__ import annotations

import json

import jsonschema
import pytest
import yaml
from conftest import TPCH_TABLES, FakeWorkspaceClient

from genie_ontology_modeled_knowledge_sdk import __version__
from genie_ontology_modeled_knowledge_sdk.config import (
    DEFAULT_MAX_METRIC_VIEWS_PER_AGENT,
    SdkConfig,
    check_access,
    config_from_dict,
    expand_tables,
    load_config,
    load_schema,
    validate_config,
)

# --- schema and validate_config -------------------------------------------------


def test_version():
    assert __version__ == "0.1.1"


def test_schema_is_draft_2020_12_and_accepts_tpch_config(tpch_config):
    schema = load_schema()
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(tpch_config)  # raises if invalid
    assert validate_config(tpch_config) == []


def test_schema_rejects_config_with_no_source_inputs(tpch_config):
    del tpch_config["source_tables"]
    validator = jsonschema.Draft202012Validator(load_schema())
    assert not validator.is_valid(tpch_config)
    errors = validate_config(tpch_config)
    assert len(errors) == 1
    assert "at least one of source_catalogs, source_schemas, source_tables" in errors[0]


def test_empty_source_lists_count_as_missing(tpch_config):
    tpch_config.update(source_tables=[], source_schemas=[], source_catalogs=[])
    errors = validate_config(tpch_config)
    assert any("at least one of source_catalogs" in e for e in errors)


@pytest.mark.parametrize("key", ["source_catalogs", "source_schemas", "source_tables"])
def test_any_single_source_input_is_enough(key):
    value = {
        "source_catalogs": ["samples"],
        "source_schemas": ["samples.tpch"],
        "source_tables": ["samples.tpch.orders"],
    }[key]
    d = {"target_catalog": "main", "target_schema": "s", "domain_name": "d", "domain_context": "ctx", key: value}
    assert validate_config(d) == []


@pytest.mark.parametrize("key", ["target_catalog", "target_schema", "domain_name", "domain_context"])
def test_required_fields(tpch_config, key):
    del tpch_config[key]
    errors = validate_config(tpch_config)
    assert errors and any(key in e for e in errors)


@pytest.mark.parametrize("name", ["TpchSupply", "tpch-supply", "1tpch", "tpch supply"])
def test_domain_name_must_be_snake_case(tpch_config, name):
    tpch_config["domain_name"] = name
    errors = validate_config(tpch_config)
    assert any(e.startswith("domain_name:") for e in errors)


def test_two_part_table_name_is_an_error(tpch_config):
    tpch_config["source_tables"] = ["samples.tpch.orders", "tpch.lineitem"]
    errors = validate_config(tpch_config)
    assert errors == ["source_tables[1]: 'tpch.lineitem' must be a 3-part name catalog.schema.table"]


def test_table_name_with_empty_part_is_an_error(tpch_config):
    tpch_config["source_tables"] = ["samples..orders"]
    assert validate_config(tpch_config) == [
        "source_tables[0]: 'samples..orders' must be a 3-part name catalog.schema.table"
    ]


def test_schema_names_must_be_two_part(tpch_config):
    tpch_config["source_schemas"] = ["tpch"]
    assert validate_config(tpch_config) == ["source_schemas[0]: 'tpch' must be a 2-part name catalog.schema"]


def test_unknown_keys_and_bad_types_are_rejected(tpch_config):
    tpch_config["surprise"] = True
    tpch_config["max_metric_views_per_agent"] = 0
    tpch_config["supplemental_volume_dirs"] = ["/tmp/context"]
    errors = validate_config(tpch_config)
    assert any("surprise" in e for e in errors)
    assert any(e.startswith("max_metric_views_per_agent:") for e in errors)
    assert any(e.startswith("supplemental_volume_dirs.0:") for e in errors)


def test_non_dict_config():
    assert validate_config(["not", "a", "dict"]) == ["config: must be a JSON object"]


def test_max_metric_views_above_30_warns_but_is_not_an_error(tpch_config):
    import warnings

    from genie_ontology_modeled_knowledge_sdk import geniespace
    from genie_ontology_modeled_knowledge_sdk.config import AGENT_DATA_SOURCE_LIMIT, config_warnings

    assert AGENT_DATA_SOURCE_LIMIT == geniespace.MAX_DATA_SOURCES == 30
    tpch_config["max_metric_views_per_agent"] = 31
    with pytest.warns(UserWarning, match="above 30"):
        assert validate_config(tpch_config) == []
    assert len(config_warnings(tpch_config)) == 1
    tpch_config["max_metric_views_per_agent"] = 30
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert validate_config(tpch_config) == []
    assert config_warnings(tpch_config) == [] and config_warnings([]) == []
    del tpch_config["max_metric_views_per_agent"]
    assert config_warnings(tpch_config) == []


# --- SdkConfig, config_from_dict, load_config ---------------------------------------


def test_config_from_dict_applies_defaults(tpch_config):
    del tpch_config["max_metric_views_per_agent"]
    cfg = config_from_dict(tpch_config)
    assert isinstance(cfg, SdkConfig)
    assert cfg.max_metric_views_per_agent == DEFAULT_MAX_METRIC_VIEWS_PER_AGENT == 50
    assert cfg.source_catalogs == [] and cfg.warehouse_id is None
    assert cfg.source_tables == [f"samples.tpch.{t}" for t in TPCH_TABLES]


def test_config_from_dict_raises_with_all_problems():
    with pytest.raises(ValueError) as exc:
        config_from_dict({"domain_name": "Bad-Name"})
    msg = str(exc.value)
    assert "target_catalog" in msg and "domain_name" in msg and "source_catalogs" in msg


def test_to_dict_round_trip(tpch_config):
    cfg = config_from_dict(tpch_config)
    d = cfg.to_dict()
    assert "warehouse_id" not in d and "source_catalogs" not in d  # None / empty omitted
    assert validate_config(d) == []
    assert config_from_dict(d) == cfg


def test_load_config_json_and_yaml(tmp_path, tpch_config):
    jpath = tmp_path / "sdk_config.json"
    jpath.write_text(json.dumps(tpch_config))
    ypath = tmp_path / "sdk_config.yml"
    ypath.write_text(yaml.safe_dump(tpch_config))
    assert load_config(jpath) == load_config(str(ypath)) == config_from_dict(tpch_config)


def test_load_config_invalid_file_raises(tmp_path):
    p = tmp_path / "sdk_config.json"
    p.write_text(json.dumps({"target_catalog": "main"}))
    with pytest.raises(ValueError):
        load_config(p)


# --- expand_tables -------------------------------------------------------------


def test_expand_tables_from_tables_is_sorted_unique(tpch_config, fake_ws):
    tpch_config["source_schemas"] = ["samples.tpch"]  # overlaps every source_tables entry
    tables = expand_tables(tpch_config, fake_ws)
    assert tables == sorted(f"samples.tpch.{t}" for t in TPCH_TABLES)


def test_expand_tables_from_schemas_and_catalogs(fake_ws):
    base = {"target_catalog": "main", "target_schema": "s", "domain_name": "d", "domain_context": "c"}
    from_schema = expand_tables({**base, "source_schemas": ["samples.tpch"]}, fake_ws)
    assert from_schema == sorted(f"samples.tpch.{t}" for t in TPCH_TABLES)

    from_catalog = expand_tables(
        {**base, "source_catalogs": ["samples"], "source_tables": ["samples.tpch.orders"]}, fake_ws
    )
    assert "samples.nyctaxi.trips" in from_catalog
    assert not any(".information_schema." in t for t in from_catalog)
    assert len(from_catalog) == len(TPCH_TABLES) + 1
    assert from_catalog == sorted(set(from_catalog))


# --- check_access ---------------------------------------------------------------


def test_check_access_ok(tpch_config, fake_ws):
    tpch_config["supplemental_volume_dirs"] = ["/Volumes/main/ontology_tpch/context"]
    tpch_config["source_catalogs"] = ["samples"]
    tpch_config["source_schemas"] = ["samples.tpch"]
    assert check_access(tpch_config, fake_ws) == []
    assert check_access(config_from_dict(tpch_config), fake_ws) == []


def test_check_access_problem_messages(tpch_config, fake_ws):
    tpch_config.update(
        source_catalogs=["nope_catalog"],
        source_schemas=["samples.nope"],
        source_tables=["samples.tpch.orders", "samples.tpch.missing"],
        target_catalog="absent_target",
        supplemental_volume_dirs=["/Volumes/main/ontology_tpch/missing_dir"],
    )
    problems = check_access(tpch_config, fake_ws)
    assert len(problems) == 5
    expected_prefixes = [
        "source catalog 'nope_catalog': not found or not accessible",
        "source schema 'samples.nope': not found or not accessible",
        "source table 'samples.tpch.missing': not found or not accessible",
        "target catalog 'absent_target': not found or not accessible",
        "supplemental volume dir '/Volumes/main/ontology_tpch/missing_dir': not found or not accessible",
    ]
    for prefix, problem in zip(expected_prefixes, problems, strict=False):
        assert problem.startswith(prefix), problem
    assert "does not exist" in problems[0]  # underlying error is kept


def test_check_access_never_raises(tpch_config):
    class Exploding:
        def __getattr__(self, name):
            raise RuntimeError("client is broken")

    problems = check_access(tpch_config, Exploding())
    assert problems and all(isinstance(p, str) for p in problems)

    # an invalid config is reported, not raised
    assert check_access({"target_catalog": "main"}, FakeWorkspaceClient())[0].startswith("config:")


def test_check_access_permission_denied_is_reported(tpch_config, fake_ws):
    def denied(name):
        raise PermissionError("User does not have USE CATALOG on catalog 'samples'")

    fake_ws.tables.get = denied
    problems = check_access(tpch_config, fake_ws)
    assert len(problems) == len(TPCH_TABLES)
    assert "USE CATALOG" in problems[0]
