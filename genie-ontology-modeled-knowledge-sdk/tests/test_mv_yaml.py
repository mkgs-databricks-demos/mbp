"""Tests for genie_ontology_modeled_knowledge_sdk.mv_yaml (rules MV001-MV007, substitution, DDL, CLI)."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
import yaml

from genie_ontology_modeled_knowledge_sdk import mv_yaml
from genie_ontology_modeled_knowledge_sdk.mv_yaml import (
    Finding,
    has_errors,
    load_mv,
    load_mv_text,
    render_ddl,
    strip_sdk_only_keys,
    substitute,
    validate_file,
    validate_mv,
)

REPO = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "metric_views"
GOOD = FIXTURES / "good"
BAD = FIXTURES / "bad"
WARN = FIXTURES / "warn"
SALES = GOOD / "sales" / "mv_sales_revenue.yml"
TPCH = GOOD / "tpch_supply_chain" / "orders" / "mv_tpch_order_lines.yml"

PARAMS = {
    "source_catalog": "dev_src",
    "source_schema": "sales_src",
    "target_catalog": "dev_tgt",
    "target_schema": "ontology",
}


def errors(findings):
    return {f.rule for f in findings if f.severity == "error"}


def warnings(findings):
    return {f.rule for f in findings if f.severity == "warning"}


def mv(body: str) -> str:
    return textwrap.dedent(body).lstrip()


BASE = mv("""
    version: 1.1
    source: ${source_catalog}.${source_schema}.orders
    dimensions:
      - name: Order Priority
        expr: source.o_orderpriority
    measures:
      - name: Order Count
        expr: COUNT(1)
        comment: "Number of orders"
""")


# ------------------------------------------------------------------ fixtures


def test_fixture_dirs_cover_every_rule():
    bad_rules = {p.name[:5].upper() for p in BAD.glob("*.yml")}
    warn_rules = {p.name[:5].upper() for p in WARN.glob("*.yml")}
    assert bad_rules | warn_rules == {f"MV00{i}" for i in range(1, 8)}
    assert len(list(GOOD.rglob("*.yml"))) >= 3


@pytest.mark.parametrize("path", sorted(GOOD.rglob("*.yml")), ids=lambda p: p.stem)
def test_good_fixtures_have_no_findings(path):
    assert validate_file(path) == []


@pytest.mark.parametrize("path", sorted(BAD.glob("*.yml")), ids=lambda p: p.stem)
def test_bad_fixtures_fail_only_their_rule(path):
    rule = path.name[:5].upper()
    assert errors(validate_file(path)) == {rule}


@pytest.mark.parametrize("path", sorted(WARN.glob("*.yml")), ids=lambda p: p.stem)
def test_warn_fixtures_warn_only_their_rule(path):
    rule = path.name[:5].upper()
    findings = validate_file(path)
    assert errors(findings) == set()
    assert warnings(findings) == {rule}


def test_base_doc_is_clean():
    assert validate_mv(BASE, name="mv_orders") == []


def test_load_mv_returns_dict_with_tokens_intact():
    doc = load_mv(SALES)
    assert doc["source"] == "${source_catalog}.${source_schema}.orders"
    assert doc["version"] == 1.1


def test_load_mv_keeps_on_as_a_string_key():
    doc = load_mv(SALES)
    assert doc["joins"][0]["on"] == "source.customer_id = customer.customer_id"
    assert True not in doc["joins"][0]
    assert doc["joins"][0]["rely"]["at_most_one_match"] is True


def test_validate_accepts_yaml11_parsed_on_key():
    doc = yaml.safe_load(JOIN_RELY)  # PyYAML default: `on` -> True
    assert True in doc["joins"][0]
    assert errors(validate_mv(doc, name="mv_orders")) == set()


def test_load_mv_rejects_non_mapping(tmp_path):
    p = tmp_path / "x.yml"
    p.write_text("- a\n- b\n")
    with pytest.raises(ValueError):
        load_mv(p)


def test_finding_shape():
    f = validate_mv(BASE.replace("version: 1.1", "version: 1"), name="mv_orders")[0]
    assert isinstance(f, Finding)
    assert f.to_dict() == {"rule": "MV001", "severity": "error", "message": f.message}
    assert f["rule"] == "MV001" and f["severity"] == "error"
    assert str(f).startswith("ERROR MV001:")


# ---------------------------------------------------------------------- MV001


@pytest.mark.parametrize(
    "change",
    [
        lambda t: t.replace("version: 1.1", "version: 1"),
        lambda t: t.replace("version: 1.1\n", ""),
        lambda t: t.replace("source: ${source_catalog}.${source_schema}.orders\n", ""),
        lambda t: t + "unexpected_key: 1\n",
        lambda t: t + "fields:\n  - name: X\n    expr: source.x\n",
        lambda t: t.replace("    expr: COUNT(1)\n", ""),
    ],
    ids=["int-version", "no-version", "no-source", "unknown-key", "dims-and-fields", "no-expr"],
)
def test_mv001_failures(change):
    assert "MV001" in errors(validate_mv(change(BASE), name="mv_orders"))


def test_mv001_requires_dimensions_or_measures():
    doc = {"version": 1.1, "source": "${source_catalog}.${source_schema}.orders"}
    assert errors(validate_mv(doc, name="mv_orders")) == {"MV001"}


def test_mv001_measures_only_and_quoted_version_pass():
    text = mv("""
        version: "1.1"
        source: ${source_catalog}.${source_schema}.orders
        measures:
          - name: Order Count
            expr: COUNT(1)
            comment: "Number of orders"
    """)
    assert validate_mv(text, name="mv_orders") == []


def test_mv001_invalid_view_name_and_yaml():
    assert errors(validate_mv(BASE, name="mv-orders")) == {"MV001"}
    assert errors(validate_mv("version: [1.1\n", name="mv_orders")) == {"MV001"}


# ---------------------------------------------------------------------- MV002


def test_mv002_duplicate_join_names():
    text = BASE + mv("""
        joins:
          - name: customer
            source: ${source_catalog}.${source_schema}.customer
            on: source.o_custkey = customer.c_custkey
          - name: Customer
            source: ${source_catalog}.${source_schema}.customer
            on: source.o_custkey = Customer.c_custkey
    """)
    assert errors(validate_mv(text, name="mv_orders")) == {"MV002"}


def test_mv002_duplicate_dimension_names():
    text = BASE.replace(
        "measures:",
        "  - name: order priority\n    expr: source.o_orderpriority\nmeasures:",
    )
    assert errors(validate_mv(text, name="mv_orders")) == {"MV002"}


# ---------------------------------------------------------------------- MV003


@pytest.mark.parametrize("expr", ["source.*", '"*"', "source.* EXCEPT (o_comment)"])
def test_mv003_wildcards(expr):
    text = BASE.replace("  - name: Order Priority\n    expr: source.o_orderpriority", f"  - expr: {expr}")
    assert errors(validate_mv(text, name="mv_orders")) == {"MV003"}


def test_mv003_implicit_name():
    text = BASE.replace("  - name: Order Priority\n    expr: source.o_orderpriority", "  - expr: o_orderpriority")
    assert errors(validate_mv(text, name="mv_orders")) == {"MV003"}


def test_mv003_select_star_sql_source():
    text = BASE.replace(
        "source: ${source_catalog}.${source_schema}.orders",
        "source: SELECT * FROM ${source_catalog}.${source_schema}.orders",
    )
    assert errors(validate_mv(text, name="mv_orders")) == {"MV003"}


def test_mv003_count_star_is_not_a_wildcard():
    text = BASE.replace("COUNT(1)", "COUNT(*)")
    assert validate_mv(text, name="mv_orders") == []


# ---------------------------------------------------------------------- MV004


@pytest.mark.parametrize(
    "source",
    [
        "samples.tpch.orders",
        "orders",
        "${source_schema}.orders",
        "${source_catalogue}.${source_schema}.orders",
        "SELECT o_orderkey, o_orderpriority FROM samples.tpch.orders",
    ],
    ids=["literal-3part", "bare", "2part", "unknown-token", "sql-literal"],
)
def test_mv004_failures(source):
    text = BASE.replace("${source_catalog}.${source_schema}.orders", source)
    assert "MV004" in errors(validate_mv(text, name="mv_orders"))


def test_mv004_hardcoded_join_source():
    text = BASE + mv("""
        joins:
          - name: customer
            source: main.tpch.customer
            on: source.o_custkey = customer.c_custkey
    """)
    assert errors(validate_mv(text, name="mv_orders")) == {"MV004"}


def test_mv004_nested_join_source_is_checked():
    doc = load_mv(TPCH)
    doc["joins"][0]["joins"][0]["source"] = "samples.tpch.customer"
    assert errors(validate_mv(doc, name="mv_tpch_order_lines", text=TPCH.read_text())) == {"MV004"}


def test_mv004_literal_schema_is_a_warning():
    text = BASE.replace("${source_catalog}.${source_schema}.orders", "${source_catalog}.tpch.orders")
    findings = validate_mv(text, name="mv_orders")
    assert errors(findings) == set() and warnings(findings) == {"MV004"}


def test_mv004_target_catalog_source_allowed():
    text = BASE.replace("${source_catalog}.${source_schema}.orders", "${target_catalog}.${target_schema}.mv_base")
    assert validate_mv(text, name="mv_orders") == []


# ---------------------------------------------------------------------- MV005

JOIN_RELY = BASE + mv("""
    joins:
      - name: customer
        source: ${source_catalog}.${source_schema}.customer
        on: source.o_custkey = customer.c_custkey
        rely:
          at_most_one_match: true
""")


def test_mv005_rely_without_evidence_warns():
    findings = validate_mv(JOIN_RELY, name="mv_orders")
    assert errors(findings) == set() and warnings(findings) == {"MV005"}


def test_mv005_verified_comment_passes():
    text = JOIN_RELY.replace("    rely:", "    # verified: many_to_one, 0 orphans\n    rely:")
    assert "# verified:" in text
    assert validate_mv(text, name="mv_orders") == []


def test_mv005_verified_comment_on_item_line_passes():
    text = JOIN_RELY.replace("  - name: customer\n", "  - name: customer  # verified: many_to_one\n")
    assert validate_mv(text, name="mv_orders") == []


def test_mv005_verified_cardinality_field_passes():
    doc = load_mv_text(JOIN_RELY)
    doc["joins"][0]["verified_cardinality"] = "many_to_one"
    assert validate_mv(doc, name="mv_orders") == []


def test_mv005_dict_without_text_cannot_see_comments():
    text = JOIN_RELY.replace("    rely:", "    # verified: many_to_one\n    rely:")
    assert "# verified:" in text
    assert warnings(validate_mv(load_mv_text(text), name="mv_orders")) == {"MV005"}
    assert validate_mv(load_mv_text(text), name="mv_orders", text=text) == []


def test_mv005_comment_of_other_join_does_not_count():
    # a sibling join below `customer` carries the comment; `customer` still warns
    text = JOIN_RELY + (
        "  - name: nation\n"
        "    source: ${source_catalog}.${source_schema}.nation\n"
        "    # verified: many_to_one\n"
        "    on: source.o_custkey = nation.n_nationkey\n"
    )
    assert warnings(validate_mv(text, name="mv_orders")) == {"MV005"}


def test_mv005_using_passes_and_both_fails():
    using = (
        BASE
        + "joins:\n  - name: customer\n    source: ${source_catalog}.${source_schema}.customer\n"
        + "    using:\n      - o_custkey\n"
    )
    assert validate_mv(using, name="mv_orders") == []
    both = using + "    on: source.o_custkey = customer.o_custkey\n"
    assert errors(validate_mv(both, name="mv_orders")) == {"MV005"}


# ---------------------------------------------------------------------- MV006


def test_mv006_blank_comment_warns():
    text = BASE.replace('comment: "Number of orders"', 'comment: "  "')
    findings = validate_mv(text, name="mv_orders")
    assert errors(findings) == set() and warnings(findings) == {"MV006"}


# ---------------------------------------------------------------------- MV007

MAT = BASE + mv("""
    materialization:
      mode: relaxed
      materialized_views:
        - name: by_priority
          type: aggregated
          dimensions:
            - Order Priority
          measures:
            - Order Count
          refresh_policy: auto
""")


def test_mv007_valid_block_passes():
    assert validate_mv(MAT, name="mv_orders") == []


@pytest.mark.parametrize(
    "change",
    [
        lambda t: t.replace("refresh_policy: auto", "refresh_policy: sometimes"),
        lambda t: t.replace("mode: relaxed", "mode: strict"),
        lambda t: t.replace("        - Order Priority", "        - Missing Dim"),
        lambda t: t.replace("        - Order Priority", "        - Order Count"),
        lambda t: t.replace("        - Order Priority", '        - "*"'),
        lambda t: t.replace("        - Order Count\n      refresh", "        - Nope\n      refresh"),
        lambda t: t.replace("version: 1.1", "version: 0.1"),
        lambda t: t + "parameters:\n  - name: min_amount\n    data_type: INT\n",
        lambda t: t + "      cluster_by:\n        auto: true\n      partition_by:\n        - x\n",
    ],
    ids=[
        "bad-policy",
        "bad-mode",
        "unknown-dim",
        "measure-as-dim",
        "wildcard-dims",
        "unknown-measure",
        "policy-needs-1.1",
        "parameters",
        "cluster-and-partition",
    ],
)
def test_mv007_failures(change):
    assert "MV007" in errors(validate_mv(change(MAT), name="mv_orders"))


def test_mv007_unaggregated_rules():
    doc = load_mv_text(MAT)
    doc["materialization"]["materialized_views"] = [
        {"name": "base", "type": "unaggregated", "refresh_policy": "incremental strict"},
    ]
    assert validate_mv(doc, name="mv_orders") == []
    doc["materialization"]["materialized_views"].append(
        {"name": "base2", "type": "unaggregated", "refresh_policy": "full", "dimensions": ["Order Priority"]}
    )
    msgs = [f.message for f in validate_mv(doc, name="mv_orders") if f.rule == "MV007"]
    assert any("only one unaggregated" in m for m in msgs)
    assert any("does not list dimensions" in m for m in msgs)


@pytest.mark.parametrize(
    "name,expr,categorical",
    [
        ("Customer ID", "source.customer_id", False),
        ("Cust", "source.c_custkey", False),
        ("Cust", "source.customerId", False),
        ("Is Paid", "source.is_paid", True),
        ("Market Segment", "source.c_mktsegment", True),
        ("Order Month", "DATE_TRUNC('MONTH', source.order_date)", True),
    ],
)
def test_mv007_categorical_heuristic(name, expr, categorical):
    doc = load_mv_text(MAT)
    doc["dimensions"] = [{"name": name, "expr": expr}]
    doc["materialization"]["materialized_views"][0]["dimensions"] = [name]
    assert ("MV007" not in errors(validate_mv(doc, name="mv_orders"))) is categorical


# ---------------------------------------------------------------- substitute


def test_substitute_replaces_all_occurrences():
    out = substitute("${source_catalog}.${source_schema}.a, ${source_catalog}.x.b", PARAMS)
    assert out == "dev_src.sales_src.a, dev_src.x.b"


def test_substitute_ignores_unused_params_and_plain_dollars():
    assert substitute("price $5 and $x", PARAMS) == "price $5 and $x"


@pytest.mark.parametrize("text", ["${missing}.a", "${}.a", "${ source_catalog }.a", "${source_catalog.a"])
def test_substitute_unresolved_raises(text):
    with pytest.raises(ValueError, match="unresolved"):
        substitute(text, PARAMS)


def test_substitute_names_every_unresolved_token():
    with pytest.raises(ValueError) as exc:
        substitute("${a}.${b}.${a}", {})
    assert "${a}" in str(exc.value) and "${b}" in str(exc.value)


@pytest.mark.parametrize("value", ["main; DROP TABLE x", "a.b", "${source_schema}", "", "`a`b`"])
def test_substitute_rejects_unsafe_values(value):
    with pytest.raises(ValueError, match="unsafe"):
        substitute("${source_catalog}.s.t", {"source_catalog": value})


def test_substitute_accepts_backticked_value():
    assert substitute("${source_catalog}.s.t", {"source_catalog": "`dev-cat`"}) == "`dev-cat`.s.t"


# ---------------------------------------------------------------- render_ddl


def test_render_ddl_sales_snapshot():
    text = SALES.read_text()
    ddl = render_ddl(text, "${target_catalog}.${target_schema}.mv_sales_revenue", PARAMS)
    expected_body = (
        text.replace("${source_catalog}", "dev_src")
        .replace("${source_schema}", "sales_src")
        .replace("${target_catalog}", "dev_tgt")
        .replace("${target_schema}", "ontology")
    )
    assert ddl == (
        "CREATE OR REPLACE VIEW dev_tgt.ontology.mv_sales_revenue\n"
        "WITH METRICS\nLANGUAGE YAML\nAS $$\n" + expected_body + "$$"
    )
    assert "${" not in ddl
    body = ddl.split("AS $$\n", 1)[1].rsplit("$$", 1)[0]
    doc = yaml.safe_load(body)
    assert doc["source"] == "dev_src.sales_src.orders"
    assert doc["joins"][0]["source"] == "dev_src.sales_src.dim_customers"


def test_render_ddl_strips_sdk_only_keys():
    ddl = render_ddl(TPCH.read_text(), "cat.sch.mv_tpch_order_lines", PARAMS)
    assert "verified_cardinality" in TPCH.read_text()
    assert not re.search(r"^\s*verified_cardinality\s*:", ddl, re.MULTILINE)
    assert "# verified:" in ddl  # comments are preserved
    body = ddl.split("AS $$\n", 1)[1].rsplit("$$", 1)[0]
    assert yaml.safe_load(body)["joins"][0]["rely"] == {"at_most_one_match": True}


def test_strip_sdk_only_keys_keeps_other_lines():
    assert strip_sdk_only_keys("a: 1\n    verified_cardinality: many_to_one\nb: 2\n") == "a: 1\nb: 2\n"


def test_render_ddl_unresolved_param_raises():
    with pytest.raises(ValueError, match="unresolved"):
        render_ddl(SALES.read_text(), "cat.sch.mv", {"source_catalog": "c", "source_schema": "s"})


@pytest.mark.parametrize("fq", ["cat.mv", "cat.sch.mv; DROP", "a.b.c.d"])
def test_render_ddl_rejects_bad_fq_name(fq):
    with pytest.raises(ValueError):
        render_ddl(BASE, fq, PARAMS)


def test_render_ddl_rejects_dollar_dollar_in_body():
    with pytest.raises(ValueError, match=r"\$\$"):
        render_ddl(BASE + "# AS $$ body $$\n", "cat.sch.mv_orders", PARAMS)


# ----------------------------------------------------------------------- CLI


def test_cli_good_exits_0(capsys):
    assert mv_yaml.main(["validate", str(GOOD)]) == 0
    assert "0 error(s)" in capsys.readouterr().out


def test_cli_bad_exits_1(capsys):
    assert mv_yaml.main(["validate", str(BAD)]) == 1
    out = capsys.readouterr().out
    for rule in ("MV001", "MV002", "MV003", "MV004", "MV005", "MV007"):
        assert f"ERROR {rule}" in out


def test_cli_warnings_only_exits_0(capsys):
    assert mv_yaml.main(["validate", str(WARN)]) == 0
    assert "WARNING MV005" in capsys.readouterr().out


def test_cli_single_file_and_missing_and_empty(tmp_path):
    assert mv_yaml.main(["validate", str(SALES)]) == 0
    assert mv_yaml.main(["validate", str(tmp_path / "nope")]) == 2
    assert mv_yaml.main(["validate", str(tmp_path)]) == 1


def test_cli_duplicate_names_across_folders(tmp_path):
    for domain in ("a", "b"):
        (tmp_path / domain).mkdir()
        (tmp_path / domain / "mv_orders.yml").write_text(BASE)
    results = mv_yaml.validate_path(tmp_path)
    assert any(has_errors(f) for f in results.values())
    assert mv_yaml.main(["validate", str(tmp_path)]) == 1


def test_cli_module_entry_point():
    env = {**os.environ, "PYTHONPATH": str(REPO / "src")}
    good = subprocess.run(
        [sys.executable, "-m", "genie_ontology_modeled_knowledge_sdk.mv_yaml", "validate", str(GOOD)],
        env=env,
        capture_output=True,
        text=True,
    )
    bad = subprocess.run(
        [sys.executable, "-m", "genie_ontology_modeled_knowledge_sdk.mv_yaml", "validate", str(BAD)],
        env=env,
        capture_output=True,
        text=True,
    )
    assert good.returncode == 0, good.stdout + good.stderr
    assert bad.returncode == 1, bad.stdout + bad.stderr
