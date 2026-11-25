"""Tests for genie_ontology_modeled_knowledge_sdk.geniespace (sessions 03, 19)."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from genie_ontology_modeled_knowledge_sdk import geniespace as gs
from genie_ontology_modeled_knowledge_sdk.geniespace import AgentPlan, MvRef

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "geniespace"
SALES_EXAMPLE = ROOT / "examples" / "agents" / "sales_agent.geniespace.json"
HEX32 = re.compile(r"^[0-9a-f]{32}$")

DOMAIN = "tpch_supply_chain"


def _mvs(n: int, subdomains: list[str], domain: str = DOMAIN) -> list[MvRef]:
    return [MvRef(name=f"mv_{i:03d}", domain=domain, subdomain=subdomains[i % len(subdomains)]) for i in range(n)]


def _small_plan() -> AgentPlan:
    mvs = [
        MvRef(name="mv_tpch_revenue", domain=DOMAIN, subdomain="sales", description="Revenue by order date"),
        MvRef(name="mv_tpch_orders", domain=DOMAIN, subdomain="sales"),
        MvRef(name="mv_tpch_supply", domain=DOMAIN, subdomain="supply"),
    ]
    return gs.plan_agents(mvs)[0]


def _build(plan: AgentPlan) -> dict:
    return gs.build_space(
        plan,
        warehouse_id="abc",
        sample_questions=["What was total revenue last month?", "Top 10 customers by revenue"],
        text_instructions=["Use the Revenue measure for revenue questions.", "Round money to 2 decimals."],
        example_sqls=[
            {
                "question": "Top 10 customers by revenue",
                "sql": (
                    "SELECT `Customer`, MEASURE(`Revenue`) AS revenue\n"
                    "FROM ${target_catalog}.${target_schema}.mv_tpch_revenue\n"
                    "GROUP BY ALL\nORDER BY revenue DESC\nLIMIT 10"
                ),
            }
        ],
        join_specs=[{"left": {"identifier": "a.b.c"}, "right": {"identifier": "a.b.d"}, "sql": ["c.k = d.k"]}],
    )


# ----------------------------------------------------------------------------- plan_agents


def test_three_mvs_make_one_agent():
    plans = gs.plan_agents(_mvs(3, ["sales", "supply", "finance"]))
    assert len(plans) == 1
    p = plans[0]
    assert p.name == f"{DOMAIN}_agent"
    assert p.subdomain is None
    assert p.mv_names == ["mv_000", "mv_001", "mv_002"]
    assert p.related_agents == []


def test_exactly_limit_stays_single_agent():
    assert len(gs.plan_agents(_mvs(30, ["a", "b"]))) == 1
    assert len(gs.plan_agents(_mvs(31, ["a", "b"]))) == 2
    assert len(gs.plan_agents(_mvs(10, ["a", "b"]), max_per_agent=10)) == 1
    assert len(gs.plan_agents(_mvs(11, ["a", "b"]), max_per_agent=10)) == 2


def test_effective_max_per_agent_is_capped_at_data_source_limit():
    assert gs.effective_max_per_agent() == gs.MAX_DATA_SOURCES == 30
    assert gs.effective_max_per_agent(50) == 30
    assert gs.effective_max_per_agent(12) == 12
    with pytest.raises(ValueError, match="max_per_agent"):
        gs.effective_max_per_agent(0)


@pytest.mark.parametrize("n", [29, 30, 31, 50])
@pytest.mark.parametrize("subdomains", [["sales", "supply"], ["sales"], [None]])
def test_split_limit_agents_all_pass_validate_space(n, subdomains):
    mvs = [MvRef(name=f"mv_{i:03d}", domain=DOMAIN, subdomain=subdomains[i % len(subdomains)]) for i in range(n)]
    plans = gs.plan_agents(mvs, max_per_agent=50)
    assert len(plans) == (1 if n <= 30 else 2)
    placed = [name for p in plans for name in p.mv_names]
    assert sorted(placed) == sorted(m.name for m in mvs) and len(placed) == len(set(placed))
    for p in plans:
        assert 1 <= len(p.metric_views) <= gs.MAX_DATA_SOURCES
        assert gs.validate_space(gs.build_space(p, sample_questions=["q"])) == [], p.name


def test_90_mvs_over_three_subdomains_make_three_agents_without_duplicates():
    mvs = _mvs(90, ["sales", "supply", "finance"])
    plans = gs.plan_agents(mvs, max_per_agent=50)
    assert [p.subdomain for p in plans] == ["finance", "sales", "supply"]
    assert [p.name for p in plans] == [f"{DOMAIN}_finance_agent", f"{DOMAIN}_sales_agent", f"{DOMAIN}_supply_agent"]
    placed = [n for p in plans for n in p.mv_names]
    assert len(placed) == len(set(placed)) == 90
    assert set(placed) == {m.name for m in mvs}
    assert all(len(p.metric_views) <= 30 for p in plans)
    for p in plans:
        assert all(mv.subdomain == p.subdomain for mv in p.metric_views)
        assert sorted(p.related_agents) == sorted(q.name for q in plans if q is not p)


def test_oversized_subdomain_is_split_into_numbered_agents():
    mvs = _mvs(110, ["sales"]) + [MvRef(name="mv_supply_x", domain=DOMAIN, subdomain="supply")]
    plans = gs.plan_agents(mvs, max_per_agent=50)
    names = [p.name for p in plans]
    assert names == [
        f"{DOMAIN}_sales_1_agent",
        f"{DOMAIN}_sales_2_agent",
        f"{DOMAIN}_sales_3_agent",
        f"{DOMAIN}_sales_4_agent",
        f"{DOMAIN}_supply_agent",
    ]
    assert [len(p.metric_views) for p in plans] == [30, 30, 30, 20, 1]
    placed = [n for p in plans for n in p.mv_names]
    assert len(placed) == len(set(placed)) == 111


def test_cross_domain_mv_goes_to_its_subdomain_agent():
    mvs = _mvs(60, ["sales", "supply"]) + [MvRef(name="mv_finance_margin", domain="finance", subdomain="sales")]
    plans = gs.plan_agents(mvs)
    owners = [p for p in plans if "mv_finance_margin" in p.mv_names]
    assert len(owners) == 1
    assert owners[0].subdomain == "sales"
    assert owners[0].domain == DOMAIN  # agent named after the primary domain


def test_missing_subdomain_goes_to_general():
    mvs = [MvRef(name=f"mv_{i}", domain=DOMAIN, subdomain=None if i % 2 else "sales") for i in range(6)]
    plans = gs.plan_agents(mvs, max_per_agent=4)
    assert {p.subdomain for p in plans} == {"general", "sales"}


def test_plan_agents_rejects_bad_input():
    with pytest.raises(ValueError, match="max_per_agent"):
        gs.plan_agents(_mvs(3, ["a"]), max_per_agent=0)
    with pytest.raises(ValueError, match="duplicate"):
        gs.plan_agents([MvRef(name="mv_a"), MvRef(name="mv_a")])
    assert gs.plan_agents([]) == []


def test_mv_refs_from_manifest_entries():
    entries = [
        {
            "name": "mv_tpch_revenue",
            "yaml_path": "metric_views/x/mv_tpch_revenue.yml",
            "domain": DOMAIN,
            "subdomain": "sales",
        }
    ]
    (ref,) = gs.mv_refs_from_manifest(entries)
    assert ref == MvRef(name="mv_tpch_revenue", domain=DOMAIN, subdomain="sales")
    assert ref.identifier == "${target_catalog}.${target_schema}.mv_tpch_revenue"


# ----------------------------------------------------------------------------- build_space


def test_build_space_shape_and_tokenized_identifiers():
    doc = _build(_small_plan())
    assert doc["version"] == 2
    idents = [t["identifier"] for t in doc["data_sources"]["tables"]]
    assert idents == sorted(idents)
    assert all(i.startswith("${target_catalog}.${target_schema}.mv_tpch_") for i in idents)
    rev = next(t for t in doc["data_sources"]["tables"] if t["identifier"].endswith("mv_tpch_revenue"))
    assert rev["description"] == ["Revenue by order date"]
    assert len(doc["instructions"]["text_instructions"]) == 1
    ex = doc["instructions"]["example_question_sqls"][0]
    assert ex["sql"][0].endswith("\n") and "".join(ex["sql"]).startswith("SELECT")
    assert "warehouse_id" not in json.dumps(doc)
    assert gs.validate_space(doc) == []


def test_build_space_ids_are_deterministic_32_hex():
    doc = _build(_small_plan())
    ids = [q["id"] for q in doc["config"]["sample_questions"]]
    ids += [
        x["id"] for k in ("text_instructions", "example_question_sqls", "join_specs") for x in doc["instructions"][k]
    ]
    assert all(HEX32.match(i) for i in ids)
    assert len(set(ids)) == len(ids)
    assert gs.stable_id("What was total revenue last month?") in ids
    assert gs.stable_id("x") == gs.stable_id("x") != gs.stable_id("y")


def test_build_twice_is_byte_identical():
    a = gs.space_to_json(_build(_small_plan()))
    b = gs.space_to_json(_build(_small_plan()))
    assert a == b
    # Input order does not matter either.
    plan = _small_plan()
    plan.metric_views.reverse()
    assert gs.space_to_json(_build(plan)) == a
    assert a.endswith("\n") and json.loads(a)["version"] == 2


def test_build_space_dedupes_questions_and_instructions():
    doc = gs.build_space(
        _small_plan(),
        sample_questions=["Revenue?", "revenue?  ", "Orders?"],
        text_instructions=["Round money.", "round   MONEY."],
    )
    assert len(doc["config"]["sample_questions"]) == 2
    assert doc["instructions"]["text_instructions"][0]["content"] == ["Round money."]
    assert "instructions" not in gs.build_space(_small_plan())


# ----------------------------------------------------------------------------- validate_space


def test_sales_example_passes_validation():
    doc = json.loads(SALES_EXAMPLE.read_text(encoding="utf-8"))
    assert gs.validate_space(doc) == []


@pytest.mark.parametrize(
    "mutate, expected",
    [
        (lambda d: d.update(version=1), "version"),
        (lambda d: d["data_sources"].update(tables=[]), "1-30"),
        (lambda d: d["data_sources"].update(tables=[{"identifier": f"c.s.t{i}"} for i in range(31)]), "1-30"),
        (lambda d: d["data_sources"]["tables"][0].update(identifier="schema.table"), "3-part"),
        (lambda d: d["data_sources"]["tables"].append(copy.deepcopy(d["data_sources"]["tables"][0])), "duplicate"),
        (
            lambda d: d["config"]["sample_questions"].append(copy.deepcopy(d["config"]["sample_questions"][0])),
            "duplicate id",
        ),
        (lambda d: d["config"]["sample_questions"][0].update(id="ABC"), "32-character"),
        (lambda d: d["config"]["sample_questions"][0].update(question=[]), "non-empty"),
        (
            lambda d: d["instructions"]["text_instructions"].append(
                {"id": "0" * 32, "content": ["round MONEY to 2 decimals."]}
            ),
            "duplicate instruction",
        ),
        (lambda d: d.pop("data_sources"), "data_sources"),
    ],
)
def test_validation_errors(mutate, expected):
    doc = _build(_small_plan())
    mutate(doc)
    errors = gs.validate_space(doc)
    assert any(expected in e for e in errors), errors


def test_validate_counts_metric_views_array_and_rejects_non_object():
    doc = _build(_small_plan())
    doc["data_sources"]["metric_views"] = [{"identifier": f"c.s.mv{i}"} for i in range(28)]
    assert any("got 31" in e for e in gs.validate_space(doc))
    assert gs.validate_space([]) == ["space: must be a JSON object"]


# ----------------------------------------------------------------------------- domain manifest


def test_write_domain_manifest_shape(tmp_path):
    plans = gs.plan_agents(_mvs(90, ["sales", "supply", "finance"]))
    out = tmp_path / "docs" / "domain_manifest.yml"
    data = gs.write_domain_manifest(plans, out, descriptions={DOMAIN: "TPC-H supply chain", "sales": "Orders"})
    loaded = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert loaded == data
    (dom,) = loaded["domains"]
    assert dom["name"] == DOMAIN and dom["description"] == "TPC-H supply chain"
    assert [s["name"] for s in dom["subdomains"]] == ["finance", "sales", "supply"]
    sales = dom["subdomains"][1]
    assert sales["agent"] == f"{DOMAIN}_sales_agent" and sales["description"] == "Orders"
    assert len(sales["metric_views"]) == 30
    single = gs.domain_manifest(gs.plan_agents(_mvs(3, ["a"])))
    assert [s["name"] for s in single["domains"][0]["subdomains"]] == ["a"]
    unlabelled = gs.domain_manifest(gs.plan_agents([MvRef(name="mv_x", domain=DOMAIN)]))
    assert unlabelled["domains"][0]["subdomains"] == [
        {"name": DOMAIN, "metric_views": ["mv_x"], "agent": f"{DOMAIN}_agent"}
    ]


def test_single_agent_manifest_lists_every_real_subdomain():
    mvs = _mvs(6, ["sales", "supply", "fulfillment"]) + [MvRef(name="mv_loose", domain=DOMAIN)]
    plans = gs.plan_agents(mvs)
    assert len(plans) == 1
    data = gs.domain_manifest(plans, descriptions={"sales": "Orders"})
    subs = data["domains"][0]["subdomains"]
    assert [s["name"] for s in subs] == ["fulfillment", "general", "sales", "supply"]
    assert {s["agent"] for s in subs} == {f"{DOMAIN}_agent"}
    assert subs[2]["description"] == "Orders" and subs[2]["metric_views"] == ["mv_000", "mv_003"]
    assert subs[1]["metric_views"] == ["mv_loose"]
    placed = [n for s in subs for n in s["metric_views"]]
    assert sorted(placed) == sorted(m.name for m in mvs)


# ----------------------------------------------------------------------------- benchmarks


def _bench(n: int) -> list[dict]:
    return [
        {"question": f"Benchmark question {i}?", "sql": f"SELECT {i} FROM ${{target_catalog}}.${{target_schema}}.mv_x"}
        for i in range(n)
    ]


def test_benchmarks_round_trip_498_and_fail_501():
    doc = gs.build_space(_small_plan(), sample_questions=["q"], benchmarks=_bench(498))
    qs = doc["benchmarks"]["questions"]
    assert len(qs) == 498 and gs.validate_space(doc) == []
    assert qs == sorted(qs, key=lambda q: q["id"])
    assert all(HEX32.match(q["id"]) for q in qs)
    assert qs[0]["answer"][0]["format"] == "SQL" and "${target_catalog}" in qs[0]["answer"][0]["content"][0]
    again = json.loads(gs.space_to_json(doc))
    assert gs.validate_space(again) == [] and again == doc
    big = gs.build_space(_small_plan(), benchmarks=_bench(501))
    assert any("at most 500" in e and "got 501" in e for e in gs.validate_space(big))
    assert gs.validate_space(gs.build_space(_small_plan(), benchmarks=_bench(500))) == []


def test_benchmarks_accept_section_shape_and_omit_empty():
    section = {
        "questions": [
            {"id": "a" * 32, "question": ["Q1?"], "answer": [{"format": "SQL", "content": ["SELECT 1"]}]},
            {"question": "Q2?", "sql": ["SELECT\n", "2"]},
        ]
    }
    doc = gs.build_space(_small_plan(), benchmarks=section)
    assert gs.validate_space(doc) == []
    by_q = {q["question"][0]: q for q in doc["benchmarks"]["questions"]}
    assert by_q["Q1?"]["id"] == "a" * 32
    assert by_q["Q2?"]["id"] == gs.stable_id("benchmark", "Q2?")
    assert by_q["Q2?"]["answer"] == [{"content": ["SELECT\n", "2"], "format": "SQL"}]
    assert "benchmarks" not in gs.build_space(_small_plan(), benchmarks=[])
    assert "benchmarks" not in gs.build_space(_small_plan())


@pytest.mark.parametrize(
    "items, expected",
    [
        ([{"question": "Same?", "sql": "SELECT 1"}, {"question": "Same?", "sql": "SELECT 2"}], "duplicate id"),
        ([{"question": "No SQL?"}], "exactly one SQL answer"),
        ([{"question": "Blank SQL?", "sql": "   "}], "exactly one SQL answer"),
        (
            [{"id": "b" * 32, "question": ["Q?"], "answer": [{"format": "SQL", "content": [""]}]}],
            "must not be empty",
        ),
        (
            [{"id": "b" * 32, "question": ["Q?"], "answer": [{"format": "TEXT", "content": ["x"]}]}],
            "must be 'SQL'",
        ),
        (
            [
                {
                    "id": "b" * 32,
                    "question": ["Q?"],
                    "answer": [{"format": "SQL", "content": ["SELECT 1"]}, {"format": "SQL", "content": ["SELECT 2"]}],
                }
            ],
            "exactly one SQL answer",
        ),
        ([{"id": "XYZ", "question": ["Q?"], "sql": "SELECT 1"}], "32-character"),
        ([{"question": [], "sql": "SELECT 1"}], "non-empty"),
    ],
)
def test_benchmark_validation_errors(items, expected):
    errors = gs.validate_space(gs.build_space(_small_plan(), benchmarks=items))
    assert any(expected in e for e in errors), errors


def test_benchmark_id_must_not_reuse_a_sample_question_id():
    doc = gs.build_space(_small_plan(), sample_questions=["Shared?"])
    shared = doc["config"]["sample_questions"][0]["id"]
    doc = gs.build_space(
        _small_plan(),
        sample_questions=["Shared?"],
        benchmarks=[{"id": shared, "question": "Shared?", "sql": "SELECT 1"}],
    )
    assert any("also a config.sample_questions id" in e for e in gs.validate_space(doc))
    doc["benchmarks"] = []
    assert "benchmarks: must be an object" in gs.validate_space(doc)


# ----------------------------------------------------------------------------- render


def _write_tokenized(dir_: Path) -> Path:
    dir_.mkdir(parents=True, exist_ok=True)
    path = dir_ / "tpch_agent.geniespace.json"
    path.write_text(gs.space_to_json(_build(_small_plan())), encoding="utf-8")
    return path


def test_render_space_file_with_overrides_params(tmp_path):
    src = _write_tokenized(tmp_path / "agents")
    params = json.loads((FIXTURES / "variable-overrides.json").read_text(encoding="utf-8"))
    dst = gs.render_space_file(src, tmp_path / "rendered" / src.name, params)
    text = dst.read_text(encoding="utf-8")
    assert "${" not in text
    doc = json.loads(text)
    assert all(t["identifier"].startswith("main.ontology_tpch.") for t in doc["data_sources"]["tables"])
    assert gs.validate_space(doc) == []
    assert "${target_catalog}" in src.read_text(encoding="utf-8")  # source stays tokenized


def test_render_fails_on_unresolved_token(tmp_path):
    src = _write_tokenized(tmp_path / "agents")
    with pytest.raises(ValueError, match=r"\$\{target_schema\}"):
        gs.render_space_file(src, tmp_path / "out.json", {"catalog": "main"})
    assert not (tmp_path / "out.json").exists()


def test_render_text_warehouse_token_aliases_and_escaping():
    text = '{"w": "${warehouse_id}", "c": "${target_catalog}"}'
    out = gs.render_space_text(text, {"warehouse_id": "wh1", "catalog": 'odd"name', "target_catalog": "explicit"})
    assert json.loads(out) == {"w": "wh1", "c": "explicit"}
    assert json.loads(gs.render_space_text('{"c": "${target_catalog}"}', {"catalog": 'a"b'})) == {"c": 'a"b'}


def test_render_text_substitutes_any_string_raw():
    sql = "SELECT MEASURE(`Revenue`) FROM ${target_catalog}.${target_schema}.mv_tpch_revenue"
    out = gs.render_text(sql, {"catalog": "main", "schema": "ontology_tpch"})
    assert out == "SELECT MEASURE(`Revenue`) FROM main.ontology_tpch.mv_tpch_revenue"
    assert gs.render_text("a ${target_catalog} b", {"catalog": 'x"y'}) == 'a x"y b'  # no JSON escaping
    assert gs.render_text("${target_catalog}", {"catalog": 'x"y'}, json_escape=True) == 'x\\"y'
    assert gs.render_text("no tokens", {}) == "no tokens"
    with pytest.raises(ValueError, match=r"\$\{target_schema\}"):
        gs.render_text(sql, {"catalog": "main"})


# ----------------------------------------------------------------------------- render --params / --check


class _FakeStatements:
    """Answers the two information_schema queries from ``objects`` {(catalog, schema): {names}}."""

    def __init__(self, objects: dict, state: str = "SUCCEEDED"):
        self.objects = objects
        self.state = state
        self.calls: list[tuple[str, str, dict]] = []

    def execute_statement(self, *, statement, warehouse_id, parameters, wait_timeout):
        p = {item.name: item.value for item in parameters}
        self.calls.append((statement, warehouse_id, p))
        key = (p["catalog"], p["schema"])
        if "information_schema.schemata" in statement:
            rows = [[p["schema"]]] if key in self.objects else []
        else:
            asked = {v for k, v in p.items() if re.fullmatch(r"n\d+", k)}
            rows = [[n] for n in sorted(asked & self.objects.get(key, set()))]
        error = SimpleNamespace(message="boom") if self.state != "SUCCEEDED" else None
        return SimpleNamespace(
            statement_id="stmt-1",
            status=SimpleNamespace(state=SimpleNamespace(value=self.state), error=error),
            result=SimpleNamespace(data_array=rows),
        )


def _fake_ws(objects: dict, state: str = "SUCCEEDED") -> SimpleNamespace:
    return SimpleNamespace(statement_execution=_FakeStatements(objects, state))


ALL_MVS = {("main", "ontology_tpch"): {"mv_tpch_orders", "mv_tpch_revenue", "mv_tpch_supply"}}
RESOLVED = FIXTURES / "resolved_target.json"


def test_cli_render_with_resolved_target_params(tmp_path, capsys):
    src_dir = tmp_path / "agents"
    _write_tokenized(src_dir)
    dst = tmp_path / ".rendered"
    assert gs.main(["render", str(src_dir), str(dst), "--params", str(RESOLVED)]) == 0
    doc = json.loads(next(dst.glob("*.geniespace.json")).read_text(encoding="utf-8"))
    assert {t["identifier"] for t in doc["data_sources"]["tables"]} == {
        f"main.ontology_tpch.{n}" for n in ALL_MVS[("main", "ontology_tpch")]
    }


def test_cli_render_flags_alone_and_override_params(tmp_path):
    src_dir = tmp_path / "agents"
    _write_tokenized(src_dir)
    assert gs.main(["render", str(src_dir), str(tmp_path / "a"), "--catalog", "dev", "--schema", "s1"]) == 0
    text = next((tmp_path / "a").glob("*.json")).read_text(encoding="utf-8")
    assert "dev.s1.mv_tpch_revenue" in text
    assert gs.main(["render", str(src_dir), str(tmp_path / "b"), "--params", str(RESOLVED), "--schema", "s2"]) == 0
    assert "main.s2.mv_tpch_revenue" in next((tmp_path / "b").glob("*.json")).read_text(encoding="utf-8")
    assert gs.main(["render", str(src_dir), str(tmp_path / "c")]) == 1
    assert not (tmp_path / "c").exists()


def test_cli_render_check_passes_when_every_identifier_resolves(tmp_path, capsys):
    src_dir = tmp_path / "agents"
    _write_tokenized(src_dir)
    ws = _fake_ws(ALL_MVS)
    dst = tmp_path / ".rendered"
    assert gs.main(["render", str(src_dir), str(dst), "--params", str(RESOLVED), "--check"], ws=ws) == 0
    assert "3 identifiers resolve" in capsys.readouterr().out
    assert len(list(dst.glob("*.geniespace.json"))) == 1
    calls = ws.statement_execution.calls
    assert {c[1] for c in calls} == {"wh_test"}
    # values are bound parameters, never interpolated into the statement text
    assert all("ontology_tpch" not in c[0] and "mv_tpch" not in c[0] for c in calls)


def test_cli_render_check_fails_listing_missing_identifier(tmp_path, capsys):
    src_dir = tmp_path / "agents"
    _write_tokenized(src_dir)
    ws = _fake_ws({("main", "ontology_tpch"): {"mv_tpch_orders", "mv_tpch_revenue"}})
    dst = tmp_path / ".rendered"
    assert gs.main(["render", str(src_dir), str(dst), "--params", str(RESOLVED), "--check"], ws=ws) == 1
    err = capsys.readouterr().err
    assert "main.ontology_tpch.mv_tpch_supply: not found" in err and "mv_tpch_revenue" not in err
    assert not dst.exists()


def test_cli_render_check_missing_schema_and_no_warehouse(tmp_path, capsys):
    src_dir = tmp_path / "agents"
    _write_tokenized(src_dir)
    assert (
        gs.main(["render", str(src_dir), str(tmp_path / "o"), "--params", str(RESOLVED), "--check"], ws=_fake_ws({}))
        == 1
    )
    err = capsys.readouterr().err
    assert "schema main.ontology_tpch: not found" in err and "main.ontology_tpch.mv_tpch_orders: not found" in err
    args = ["render", str(src_dir), str(tmp_path / "p"), "--catalog", "main", "--schema", "ontology_tpch", "--check"]
    assert gs.main(args, ws=_fake_ws(ALL_MVS)) == 1
    assert "needs a warehouse_id" in capsys.readouterr().err
    assert gs.main([*args, "--warehouse-id", "wh"], ws=_fake_ws(ALL_MVS, state="FAILED")) == 1
    assert "FAILED: boom" in capsys.readouterr().err


def test_check_identifiers_target_and_unresolved_tokens():
    ws = _fake_ws({("main", "ontology_tpch"): {"mv_a"}})
    problems = gs.check_identifiers(
        ["MAIN.ontology_tpch.MV_A", "${target_catalog}.${target_schema}.mv_b"], ws, "wh", target=("main", "other")
    )
    assert problems == [
        "'${target_catalog}.${target_schema}.mv_b': not a resolved 3-part name",
        "schema main.other: not found (or not visible to this user)",
    ]
    assert gs.space_identifiers(
        {"data_sources": {"tables": [{"identifier": "a.b.c"}], "metric_views": [{"identifier": "a.b.d"}]}}
    ) == ["a.b.c", "a.b.d"]


def test_cli_render(tmp_path, capsys):
    src_dir = tmp_path / "agents"
    _write_tokenized(src_dir)
    dst_dir = tmp_path / ".rendered"
    assert gs.main(["render", str(src_dir), str(dst_dir), "--params", str(FIXTURES / "variable-overrides.json")]) == 0
    rendered = list(dst_dir.glob("*.geniespace.json"))
    assert len(rendered) == 1 and "${" not in rendered[0].read_text(encoding="utf-8")

    missing = tmp_path / "missing.json"
    missing.write_text(json.dumps({"catalog": "main"}), encoding="utf-8")
    other_dst = tmp_path / "other"
    assert gs.main(["render", str(src_dir), str(other_dst), "--params", str(missing)]) == 1
    assert "unresolved tokens" in capsys.readouterr().err
    assert not other_dst.exists()
    assert gs.main(["render", str(tmp_path / "nope"), str(other_dst), "--params", str(missing)]) == 1
