"""Tests for genie_ontology_modeled_knowledge_sdk.benchmark (fake Genie client, no live API calls)."""

from __future__ import annotations

import itertools
import json
import threading
import time
from pathlib import Path
from types import SimpleNamespace as NS

import pytest
import yaml

import genie_ontology_modeled_knowledge_sdk.benchmark as bm
from genie_ontology_modeled_knowledge_sdk.benchmark import (
    ACCURACY_GATE,
    Question,
    Result,
    append_history,
    assign_splits,
    asymptote,
    benchmark_id,
    coverage,
    history_entry,
    load_question_set,
    load_questions,
    run_benchmark,
    run_eval,
    score,
    to_space_benchmarks,
    write_iteration_md,
    write_results_md,
)

FIXTURES = Path(__file__).parent / "fixtures" / "benchmark"
QUESTIONS = FIXTURES / "questions.yml"
MV_DIR = FIXTURES / "metric_views"
QUESTION_SET = FIXTURES / "question_set"
SPACE = "space-1"


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    """Record backoff/poll sleeps instead of sleeping; no jitter."""
    sleeps = []
    monkeypatch.setattr(bm, "_sleep", sleeps.append)
    monkeypatch.setattr(bm, "_jitter", lambda: 1.0)
    return sleeps


def _stmt(rows, columns=("c1", "c2"), state="SUCCEEDED", error=None):
    return NS(
        status=NS(state=NS(value=state), error=NS(message=error) if error else None),
        manifest=NS(schema=NS(columns=[NS(name=c) for c in columns])),
        result=NS(data_array=[list(r) for r in rows]),
    )


class FakeGenie:
    """Answers keyed by question text: ``{"sql": ..., "rows": ..., "state": ...}``,
    ``{"text": ...}`` (no SQL) or ``{"raise": Exception}``."""

    def __init__(self, answers):
        self.answers = answers
        self.calls = []
        self._results = {}
        self._ids = itertools.count(1)
        self._lock = threading.Lock()

    def start_conversation_and_wait(self, space_id, content, *, timeout=None, **_):
        with self._lock:
            self.calls.append(("start", space_id, content, timeout))
            n = next(self._ids)
        a = self.answers[content]
        if "raise" in a:
            raise a["raise"]
        atts = []
        if a.get("text"):
            atts.append(NS(attachment_id=f"t{n}", text=NS(content=a["text"]), query=None))
        if "sql" in a:
            atts.append(NS(attachment_id=f"a{n}", text=None, query=NS(query=a["sql"])))
            self._results[f"a{n}"] = _stmt(a.get("rows", []), state=a.get("state", "SUCCEEDED"), error=a.get("error"))
        return NS(
            conversation_id=f"c{n}",
            message_id=f"m{n}",
            id=f"m{n}",
            status=NS(value="COMPLETED"),
            error=None,
            attachments=atts,
        )

    def get_message_attachment_query_result(self, space_id, conversation_id, message_id, attachment_id):
        with self._lock:
            self.calls.append(("result", space_id, conversation_id, message_id, attachment_id))
        return NS(statement_response=self._results[attachment_id])


class FakeStatements:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def execute_statement(self, statement, warehouse_id, **kw):
        self.calls.append((statement, warehouse_id, kw))  # list.append is atomic under the GIL
        return _stmt(self.rows)


def _ws(answers, expected_rows=None):
    return NS(genie=FakeGenie(answers), statement_execution=FakeStatements(expected_rows or []))


@pytest.fixture
def questions():
    return load_questions(QUESTIONS)


GOOD_ANSWERS = {
    "What is total net revenue?": {"sql": "SELECT SUM(x) FROM t", "rows": [["1000.50"]]},
    "How many orders are there per order priority?": {
        "sql": "SELECT p, COUNT(*) FROM o GROUP BY p",
        "rows": [["2-HIGH", "2"], ["1-urgent", "3"]],
    },
    "Which region has the most customers?": {"sql": "SELECT r, COUNT(*) FROM c GROUP BY r", "rows": [["ASIA", "30"]]},
    "Describe the supplier table.": {"text": "The supplier table has one row per supplier."},
}


def test_load_questions(questions):
    assert [q.id for q in questions] == ["q01", "q02", "q03", "q04"]
    assert questions[0].expected_answer == 1000.5 and questions[0].tags == ["revenue"]
    assert questions[1].expected_answer == [["1-URGENT", 3], ["2-HIGH", 2]]
    assert questions[2].expected_sql.startswith("SELECT r_name") and questions[2].tags == ["region"]
    assert not questions[3].has_expectation and questions[3].tags == []


@pytest.mark.parametrize(
    "text, message",
    [
        ("- id: a\n  question: x\n- id: a\n  question: y\n", "duplicate id"),
        ("- question: x\n", "missing 'id'"),
        ("- id: a\n  question: ''\n", "empty question"),
        ("- id: a\n  question: x\n  answer: 1\n", "unknown keys"),
        ("id: a\n", "expected a YAML list"),
    ],
)
def test_load_questions_rejects_bad_input(tmp_path, text, message):
    f = tmp_path / "q.yml"
    f.write_text(text)
    with pytest.raises(ValueError, match=message):
        load_questions(f)


def test_load_questions_accepts_questions_mapping(tmp_path):
    f = tmp_path / "q.yml"
    f.write_text("questions:\n  - id: a\n    question: x\n")
    assert [q.id for q in load_questions(f)] == ["a"]


def test_run_benchmark_captures_sql_and_matches(questions):
    ws = _ws(GOOD_ANSWERS, expected_rows=[["asia", 30]])
    results = run_benchmark(SPACE, questions, ws, timeout_s=30, warehouse_id="wh")
    by_id = {r.question_id: r for r in results}
    assert by_id["q01"].sql == "SELECT SUM(x) FROM t" and by_id["q01"].matches_expected is True
    assert by_id["q02"].matches_expected is True  # row order and case ignored
    assert by_id["q03"].matches_expected is True  # compared with expected_sql rows
    assert by_id["q04"].sql_generated is False and by_id["q04"].matches_expected is None
    assert by_id["q04"].text.startswith("The supplier table")
    assert by_id["q01"].columns == ["c1", "c2"] and by_id["q01"].conversation_id
    # one conversation per question, timeout passed through
    starts = [c for c in ws.genie.calls if c[0] == "start"]
    assert len(starts) == 4 and all(c[1] == SPACE and c[3].total_seconds() == 30 for c in starts)
    assert ws.statement_execution.calls[0][1] == "wh"


def test_expected_sql_without_warehouse_is_not_evaluated(questions):
    ws = _ws(GOOD_ANSWERS)
    results = run_benchmark(SPACE, questions, ws)
    assert results[2].matches_expected is None
    assert ws.statement_execution.calls == []


def test_wrong_answers_failed_sql_and_errors_are_recorded(questions):
    answers = dict(GOOD_ANSWERS)
    answers["What is total net revenue?"] = {"sql": "SELECT 1", "rows": [["999"]]}
    answers["How many orders are there per order priority?"] = {
        "sql": "SELECT bad",
        "state": "FAILED",
        "error": "UNRESOLVED_COLUMN",
    }
    answers["Which region has the most customers?"] = {"raise": TimeoutError("timed out after 120s")}
    results = run_benchmark(SPACE, questions, _ws(answers), warehouse_id="wh")
    r1, r2, r3, r4 = results
    assert r1.sql_succeeded and r1.matches_expected is False
    assert r2.sql_generated and not r2.sql_succeeded and r2.matches_expected is False
    assert "UNRESOLVED_COLUMN" in r2.error
    assert r3.error.startswith("TimeoutError") and r3.matches_expected is False
    assert r4.error is None  # the run continued after the failure


def test_numeric_tolerance_and_scalar_in_first_row():
    assert bm._match_answer([["SUPPLIER#1", "1000.5000001"]], 1000.5)
    assert not bm._match_answer([["x"], ["1000.5"]], 1000.5)  # only the first row counts
    assert not bm._match_answer([], 1)
    assert bm._match_answer([["1,234.00"]], 1234)
    assert bm._rows_equal([["a", None]], [["A", "NULL"]])
    assert not bm._rows_equal([["a"]], [["a"], ["a"]])


def _r(qid, gen, ok, match, error=None):
    return Result(
        question_id=qid, question=qid, sql_generated=gen, sql_succeeded=ok, matches_expected=match, error=error
    )


def test_score_accuracy_uses_expectations_when_present():
    s = score(
        [
            _r("a", True, True, True),
            _r("b", True, True, False),
            _r("c", True, True, True),
            _r("d", True, False, False, error="x"),
            _r("e", True, True, None),
            _r("f", False, False, None),
        ]
    )
    assert (s.total, s.sql_generated, s.sql_succeeded) == (6, 5, 4)
    assert (s.with_expectations, s.matches_expected, s.errors) == (4, 2, 1)
    assert s.accuracy == pytest.approx(0.5) and s.accuracy_basis == "expected"
    assert not s.passes_gate


def test_score_falls_back_to_succeeded_and_handles_empty():
    s = score([_r("a", True, True, None), _r("b", True, True, None), _r("c", False, False, None)])
    assert s.accuracy == pytest.approx(2 / 3) and s.accuracy_basis == "succeeded"
    assert score([]).accuracy == 0.0
    assert score([_r(str(i), True, True, i < 7) for i in range(10)]).passes_gate  # 70% meets the gate
    assert ACCURACY_GATE == 0.70


def test_score_definition_is_documented():
    doc = bm.__doc__
    for phrase in (
        "Scoring definition",
        "accuracy",
        "with_expectations",
        "sql_succeeded / total",
        "0.70",
        "unit_mismatch",
        "eval-runs",
        "Stop rule",
        "benchmark_question_ids",
    ):
        assert phrase in doc


def test_write_results_md(tmp_path, questions):
    results = run_benchmark(SPACE, questions, _ws(GOOD_ANSWERS, expected_rows=[["ASIA", "30"]]), warehouse_id="wh")
    results[0].question = "Revenue | by region?"
    summary = score(results)
    out = write_results_md(summary, results, tmp_path / "tuning" / "benchmark_results.md")
    text = out.read_text()
    assert text.startswith("# Benchmark results")
    assert "| Accuracy | 100.0% (expected) |" in text and "| Gate (>= 70%) | pass |" in text
    assert "Revenue \\| by region?" in text  # pipes escaped in table cells
    assert "| q04 |" in text and "| n/a |" in text
    assert "```sql\nSELECT SUM(x) FROM t\n```" in text and "_No SQL generated._" in text
    header = next(line for line in text.splitlines() if line.startswith("| ID |"))
    row = next(line for line in text.splitlines() if line.startswith("| q02 |"))
    assert header.count("|") == row.count("|")  # same number of columns


# ---------------------------------------------------------------------------
# Question sets and coverage
# ---------------------------------------------------------------------------


def test_load_question_set_parses_tags_and_splits():
    qs = load_question_set(QUESTION_SET)
    assert [q.id for q in qs] == ["x001", "s001", "s002"]  # files sorted by name: cross.yml, simple.yml
    x, s1, s2 = qs
    assert x.type == "cross_view" and x.views == ["mv_orders", "mv_suppliers"]
    assert x.measures == ["mv_orders.Order Count", "mv_suppliers.Supplier Count"] and x.dimensions == ["Nation"]
    assert s1.type == "simple" and s1.views == ["mv_orders"] and s1.measures == ["Order Count"] and s1.split is None
    assert s2.split == "holdout" and s2.dimensions == ["Region"] and "returns" in s2.tags
    assert "${target_catalog}" in x.expected_sql  # tokens are kept


def test_load_question_set_rejects_cross_file_duplicates_and_bad_input(tmp_path):
    (tmp_path / "a.yml").write_text("- id: q1\n  question: x\n")
    (tmp_path / "b.yml").write_text("- id: q1\n  question: y\n")
    with pytest.raises(ValueError, match="duplicate id 'q1' \\(also in a.yml\\)"):
        load_question_set(tmp_path)
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(ValueError, match="no \\*.yml"):
        load_question_set(empty)
    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / "q.yml").write_text("- id: q1\n  question: x\n  split: train\n")
    with pytest.raises(ValueError, match="split"):
        load_question_set(bad)


ORDERS_MEASURES = ["Order Count", "Net Revenue", "Return Rate"]
ORDERS_DIMS = ["Order Year", "Region"]
SINGLE_TYPES = [t for t in bm.QUESTION_TYPES if t != "cross_view"]


def _q(qid, qtype, views, measures=(), dims=(), sql="SELECT 1"):
    tags = [f"type:{qtype}"] + [f"view:{v}" for v in views]
    tags += [f"measure:{m}" for m in measures] + [f"dimension:{d}" for d in dims]
    return Question(id=qid, question=f"question {qid}", expected_sql=sql, tags=tags)


def _set(n=100, n_cross=25, n_parts=20):
    """A question set that meets every coverage rule with the defaults."""
    qs = [
        _q(
            f"x{i:03d}",
            "cross_view",
            ["mv_orders", "mv_suppliers"],
            ["mv_orders.Net Revenue", "mv_suppliers.Supplier Count"],
            ["Nation"],
        )
        for i in range(n_cross)
    ]
    qs += [_q(f"p{i:03d}", "simple", ["mv_parts"], ["Part Count"], ["Brand"]) for i in range(n_parts)]
    for i in range(n - n_cross - n_parts):
        qs.append(
            _q(
                f"s{i:03d}",
                SINGLE_TYPES[i % len(SINGLE_TYPES)],
                ["mv_orders"],
                [ORDERS_MEASURES[i % 3]],
                [ORDERS_DIMS[i % 2]],
            )
        )
    return qs


def test_coverage_ok_for_a_complete_set():
    rep = coverage(_set(), MV_DIR)
    assert rep.ok, rep.problems
    assert rep.total == 100 and rep.cross_view == 25 and rep.cross_view_share == pytest.approx(0.25)
    assert rep.per_view == {"mv_orders": 80, "mv_parts": 20, "mv_suppliers": 25}
    assert rep.per_measure["mv_orders.Net Revenue"] >= 25 and rep.per_dimension["mv_suppliers.Nation"] == 25
    assert set(rep.type_mix) == set(bm.QUESTION_TYPES)
    assert rep.to_dict()["ok"] is True and "coverage: ok" in rep.to_text()


@pytest.mark.parametrize(
    "kwargs, problem",
    [
        ({"n": 99}, "99 questions; need at least 100"),
        ({"n": 499, "n_cross": 125}, "499 questions; at most 498 allowed"),
        ({"n_parts": 11}, "metric view mv_parts: 11 questions; need at least 12"),
        ({"n_cross": 24}, "cross-view share 24.0% (24/100)"),
    ],
)
def test_coverage_fails_on_each_rule(kwargs, problem):
    rep = coverage(_set(**kwargs), [MV_DIR])
    assert not rep.ok
    assert len(rep.problems) == 1 and rep.problems[0].startswith(problem), rep.problems


def test_coverage_reports_gaps_and_unknown_tags():
    qs = _set()
    qs = [q for q in qs if "Region" not in q.dimensions]  # Region never asked
    qs += [_q(f"e{i}", "simple", ["mv_orders"], ["Order Count"]) for i in range(100 - len(qs))]
    qs[-1].tags = ["view:mv_nope", "measure:Bogus", "dimension:mv_parts.Nope"]  # no type tag either
    qs[-2].expected_sql = None
    qs[-3].tags = ["type:trick", "view:mv_orders"]
    text = "\n".join(coverage(qs, MV_DIR).problems)
    assert "metric view mv_orders: dimensions never asked about: Region" in text
    assert "1 question(s) without a type: tag" in text
    assert "1 question(s) without expected_sql" in text
    assert "unknown types: e" in text and ":trick" in text
    assert "unknown views:" in text and ":mv_nope" in text
    assert "unknown measures:" in text and ":Bogus" in text
    assert "unknown dimensions:" in text and ":mv_parts.Nope" in text


def test_coverage_unqualified_tags_credit_the_questions_views():
    rep = coverage([_q("a", "simple", ["mv_orders"], ["order count"], ["region"])], MV_DIR)
    assert rep.per_measure["mv_orders.Order Count"] == 1 and rep.per_dimension["mv_orders.Region"] == 1
    # without a view tag, every view with that column is credited
    rep = coverage([_q("b", "simple", [], ["Supplier Count"])], MV_DIR)
    assert rep.per_measure["mv_suppliers.Supplier Count"] == 1


def test_coverage_cli(tmp_path, capsys):
    good = tmp_path / "good"
    good.mkdir()
    rows = [{"id": q.id, "question": q.question, "expected_sql": q.expected_sql, "tags": q.tags} for q in _set()]
    (good / "all.yml").write_text(yaml.safe_dump(rows, sort_keys=False))
    assert bm.main(["coverage", str(good), str(MV_DIR)]) == 0
    assert "coverage: ok" in capsys.readouterr().out
    (good / "all.yml").write_text(yaml.safe_dump(rows[:99], sort_keys=False))
    assert bm.main(["coverage", str(good), str(MV_DIR), "--json"]) == 1
    assert json.loads(capsys.readouterr().out)["ok"] is False
    assert bm.main(["coverage", str(tmp_path / "missing"), str(MV_DIR)]) == 2


# ---------------------------------------------------------------------------
# Splits and space benchmarks
# ---------------------------------------------------------------------------


def test_assign_splits_is_stable_and_explicit_split_wins():
    ids = [f"s{i:03d}" for i in range(1, 21)]
    first = assign_splits([Question(i, "x") for i in ids])
    second = assign_splits([Question(i, "x") for i in reversed(ids)])
    assert first == second
    # pinned: the split depends only on sha256(id), so it must not change between releases
    assert sorted(k for k, v in first.items() if v == "holdout") == ["s003", "s014", "s017", "s018"]
    many = assign_splits([Question(f"q{i}", "x") for i in range(1000)])
    assert 150 <= sum(v == "holdout" for v in many.values()) <= 250
    pinned = Question("s003", "x", split="tuning")
    assert assign_splits([pinned]) == {"s003": "tuning"} and pinned.split == "tuning"
    assert set(assign_splits([Question(i, "x") for i in ids], holdout=0.0).values()) == {"tuning"}
    with pytest.raises(ValueError):
        assign_splits([], holdout=1.0)


def test_to_space_benchmarks_shape():
    qs = load_question_set(QUESTION_SET)
    section = to_space_benchmarks(qs)
    items = section["questions"]
    assert [i["id"] for i in items] == sorted(i["id"] for i in items)
    by_id = {i["id"]: i for i in items}
    x = by_id[benchmark_id("x001")]
    assert x["question"] == ["Compare order count and supplier count by nation."]
    assert x["answer"][0]["format"] == "SQL" and len(x["answer"]) == 1
    assert "".join(x["answer"][0]["content"]) == qs[0].expected_sql  # tokenized SQL kept as lines
    assert all(len(i["id"]) == 32 and int(i["id"], 16) >= 0 for i in items)
    assert benchmark_id("x001") == benchmark_id("x001") != benchmark_id("x002")


def test_to_space_benchmarks_limits():
    qs = [Question(f"q{i}", f"question {i}", expected_sql="SELECT 1") for i in range(500)]
    assert len(to_space_benchmarks(qs)["questions"]) == 500
    with pytest.raises(ValueError, match="at most 500"):
        to_space_benchmarks(qs + [Question("q500", "x", expected_sql="SELECT 1")])
    with pytest.raises(ValueError, match="needs expected_sql"):
        to_space_benchmarks([Question("a", "x")])
    with pytest.raises(ValueError, match="duplicate"):
        to_space_benchmarks([Question("a", "x", expected_sql="S"), Question("a", "y", expected_sql="S")])


# ---------------------------------------------------------------------------
# Scoring: unit_mismatch and per-split accuracy
# ---------------------------------------------------------------------------


def test_unit_mismatch_is_flagged_but_still_a_miss():
    qs = [
        Question("r1", "What share of orders are returned?", expected_answer=0.25, tags=["type:ratio"]),
        Question("r2", "Return rate for ASIA?", expected_answer=0.125),
        Question("r3", "Return rate by region?", expected_answer=[["ASIA", 0.125], ["EUROPE", 0.5]]),
        Question("c1", "How many orders?", expected_answer=3),
        Question("r4", "Exact ratio?", expected_answer=0.25, tags=["type:ratio"]),
    ]
    answers = {
        qs[0].question: {"sql": "SELECT 25", "rows": [["25.0"]]},  # x100
        qs[1].question: {"sql": "SELECT 0.00125", "rows": [["0.00125"]]},  # /100
        qs[2].question: {"sql": "SELECT", "rows": [["europe", "50"], ["asia", "12.5"]]},
        qs[3].question: {"sql": "SELECT 300", "rows": [["300"]]},  # integer count: not a unit mismatch
        qs[4].question: {"sql": "SELECT 0.25", "rows": [["0.25"]]},
    }
    results = run_benchmark(SPACE, qs, _ws(answers))
    flags = {r.question_id: (r.matches_expected, r.unit_mismatch) for r in results}
    assert flags == {
        "r1": (False, True),
        "r2": (False, True),
        "r3": (False, True),
        "c1": (False, False),
        "r4": (True, False),
    }
    s = score(results)
    assert s.unit_mismatch == 3 and s.matches_expected == 1


def test_unit_mismatch_against_expected_sql_rows():
    q = Question("r", "Return rate?", expected_sql="SELECT ...")
    ws = _ws({"Return rate?": {"sql": "SELECT 12.5", "rows": [["12.5"]]}}, expected_rows=[["0.125"]])
    (r,) = run_benchmark(SPACE, [q], ws, warehouse_id="wh")
    assert r.matches_expected is False and r.unit_mismatch is True


def test_score_per_split_accuracy():
    results = [
        Result("a", "a", matches_expected=True, split="tuning"),
        Result("b", "b", matches_expected=False, split="tuning"),
        Result("c", "c", matches_expected=True, split="tuning"),
        Result("d", "d", matches_expected=True, split="holdout"),
        Result("e", "e", matches_expected=None, split="holdout"),  # no expectation: not scored
        Result("f", "f", matches_expected=False),
    ]
    s = score(results)
    assert s.tuning == {"n": 3, "correct": 2, "accuracy": pytest.approx(2 / 3)}
    assert s.holdout == {"n": 1, "correct": 1, "accuracy": 1.0}
    s = score(results, splits={"f": "holdout", "d": "tuning"})
    assert (s.tuning["n"], s.tuning["correct"]) == (4, 3) and (s.holdout["n"], s.holdout["correct"]) == (1, 0)
    assert score([]).tuning == {"n": 0, "correct": 0, "accuracy": 0.0}


# ---------------------------------------------------------------------------
# Backoff and bounded concurrency
# ---------------------------------------------------------------------------


class HttpError(Exception):
    def __init__(self, status_code, message="boom"):
        super().__init__(message)
        self.status_code = status_code


def test_with_backoff_retries_429_and_5xx(no_sleep):
    calls = iter([HttpError(429), HttpError(503), "ok"])

    def fn():
        item = next(calls)
        if isinstance(item, Exception):
            raise item
        return item

    assert bm._with_backoff(fn, base_s=2.0) == "ok"
    assert no_sleep == [2.0, 4.0]  # exponential


def test_with_backoff_does_not_retry_client_errors_and_gives_up(no_sleep):
    def bad_request():
        raise HttpError(400)

    with pytest.raises(HttpError):
        bm._with_backoff(bad_request)
    assert no_sleep == []

    def always_429():
        raise HttpError(429)

    with pytest.raises(HttpError):
        bm._with_backoff(always_429, retries=3, base_s=1.0, max_s=3.0)
    assert no_sleep == [1.0, 2.0, 3.0]  # capped at max_s


def test_with_backoff_recognizes_sdk_errors():
    errors = pytest.importorskip("databricks.sdk.errors")
    assert bm._is_retryable(errors.TooManyRequests("slow down"))
    assert not bm._is_retryable(errors.NotFound("missing"))
    assert not bm._is_retryable(TimeoutError("timed out"))


class FlakyGenie(FakeGenie):
    """Raises HTTP 429 on the first attempt of each question; tracks concurrency."""

    def __init__(self, answers):
        super().__init__(answers)
        self.seen = set()
        self.active = 0
        self.max_active = 0

    def start_conversation_and_wait(self, space_id, content, *, timeout=None, **kw):
        with self._lock:
            first = content not in self.seen
            self.seen.add(content)
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        try:
            time.sleep(0.01)
            if first:
                raise HttpError(429, "RESOURCE_EXHAUSTED")
            return super().start_conversation_and_wait(space_id, content, timeout=timeout, **kw)
        finally:
            with self._lock:
                self.active -= 1


def test_run_benchmark_bounded_concurrency_and_429_backoff(questions, no_sleep):
    many = questions * 3
    many = [Question(f"{q.id}-{i}", q.question, q.expected_sql, q.expected_answer, q.tags) for i, q in enumerate(many)]
    ws = NS(genie=FlakyGenie(GOOD_ANSWERS), statement_execution=FakeStatements([["ASIA", "30"]]))
    results = run_benchmark(SPACE, many, ws, warehouse_id="wh", max_workers=2)
    assert [r.question_id for r in results] == [q.id for q in many]  # order kept
    assert all(r.error is None for r in results)
    assert sum(r.matches_expected is True for r in results) == 9
    assert ws.genie.max_active <= 2
    assert len(no_sleep) == 4  # one 429 per distinct question text, each retried once


# ---------------------------------------------------------------------------
# Genie benchmark evaluation runs
# ---------------------------------------------------------------------------


def _sql_resp(sql, rows, state="SUCCEEDED"):
    return {
        "response": sql,
        "response_type": "SQL",
        "sql_execution_result": {
            "status": {"state": state},
            "manifest": {"schema": {"columns": [{"name": "v"}]}},
            "result": {"data_array": rows},
        },
    }


class FakeApi:
    """Fake ``ws.api_client`` for the eval-runs API: RUNNING -> DONE, two result pages."""

    def __init__(self, questions, final_status="DONE", polls_running=1, throttle_first_get=True):
        self.calls = []
        self.final_status = final_status
        self.polls_running = polls_running
        self.throttle = throttle_first_get
        b = {q.id: benchmark_id(q.id) for q in questions}
        self.items = [
            {"result_id": "r1", "benchmark_question_id": b["s001"], "question": "q1", "status": "DONE"},
            {"result_id": "r2", "benchmark_question_id": b["s002"], "question": "q2", "status": "DONE"},
            {"result_id": "r3", "benchmark_question_id": b["x001"], "question": "q3", "status": "DONE"},
            {"result_id": "r4", "benchmark_question_id": "f" * 32, "question": "Unknown?", "status": "DONE"},
        ]
        self.details = {
            "r1": {"assessment": "GOOD", "actual_response": [_sql_resp("SELECT 3", [["3"]])]},
            "r2": {
                "assessment": "BAD",
                "actual_response": [_sql_resp("SELECT 25", [["25"]]), {"response": "Rate", "response_type": "TEXT"}],
                "expected_response": [_sql_resp("SELECT 0.25", [["0.25"]])],
            },
            "r3": {"assessment": "NEEDS_REVIEW", "actual_response": [{"response": "No SQL", "response_type": "TEXT"}]},
            "r4": {"assessment": "BAD", "manual_assessment": True, "actual_response": []},
        }

    def do(self, method, path, body=None, query=None):
        self.calls.append((method, path, body, query))
        if method == "POST":
            return {"eval_run_id": "run1", "eval_run_status": "NOT_STARTED"}
        if path.endswith("/eval-runs/run1"):
            if self.throttle:
                self.throttle = False
                raise HttpError(429)
            self.polls_running -= 1
            if self.polls_running >= 0:
                return {"eval_run_id": "run1", "eval_run_status": "RUNNING", "num_done": 1}
            return {
                "eval_run_id": "run1",
                "eval_run_status": self.final_status,
                "num_questions": 4,
                "num_done": 4,
                "num_correct": 2,
                "num_needs_review": 1,
            }
        if path.endswith("/results"):
            if not (query or {}).get("page_token"):
                return {"eval_results": self.items[:2], "next_page_token": "p2"}
            return {"eval_results": self.items[2:]}
        result_id = path.rsplit("/", 1)[1]
        return {"result_id": result_id, **self.details[result_id]}


def test_run_eval_polls_pages_and_maps_results(no_sleep):
    qs = load_question_set(QUESTION_SET)
    assign_splits(qs)
    api = FakeApi(qs)
    run = run_eval(SPACE, NS(api_client=api), question_ids=["s001", "s002"], poll_s=10, questions=qs)
    post = api.calls[0]
    assert post[:2] == ("POST", f"/api/2.0/genie/spaces/{SPACE}/eval-runs")
    assert post[2] == {"benchmark_question_ids": [benchmark_id("s001"), benchmark_id("s002")]}
    assert run.eval_run_id == "run1" and run.status == "DONE" and run.num_correct == 2
    pages = [c for c in api.calls if c[1].endswith("/results")]
    assert [c[3] for c in pages] == [{"page_size": 100}, {"page_size": 100, "page_token": "p2"}]
    by_id = {r.question_id: r for r in run.results}
    assert list(by_id) == ["s001", "s002", "x001", "f" * 32]  # unmapped keeps the Genie id
    s1, s2, x1, unknown = by_id.values()
    assert s1.matches_expected is True and s1.sql == "SELECT 3" and s1.sql_succeeded and s1.rows == [["3"]]
    assert s2.matches_expected is False and s2.unit_mismatch is True and s2.text == "Rate"
    assert s2.split == "holdout" and s1.split == assign_splits([Question("s001", "x")])["s001"]
    assert x1.matches_expected is False and x1.needs_review is True and not x1.sql_generated
    assert unknown.matches_expected is True and unknown.assessment == "GOOD"  # manual assessment wins
    assert run.needs_review == ["x001"]
    # poll sleeps grow; the 429 on the first poll was retried with backoff
    assert no_sleep[0] == 10 and 2.0 in no_sleep and 15.0 in no_sleep
    s = score(run.results)
    assert (s.total, s.matches_expected, s.needs_review, s.unit_mismatch) == (4, 2, 1, 1)


def test_run_eval_without_question_ids_runs_all_and_fails_loud():
    qs = load_question_set(QUESTION_SET)
    api = FakeApi(qs, throttle_first_get=False)
    run_eval(SPACE, NS(api_client=api), questions=qs)
    assert api.calls[0][2] == {}
    with pytest.raises(RuntimeError, match="ended EVALUATION_FAILED"):
        run_eval(SPACE, NS(api_client=FakeApi(qs, final_status="EVALUATION_FAILED")), questions=qs)
    with pytest.raises(TimeoutError, match="still"):
        run_eval(SPACE, NS(api_client=FakeApi(qs, polls_running=10**6)), timeout_s=-1)


# ---------------------------------------------------------------------------
# Accuracy history and the asymptote rule
# ---------------------------------------------------------------------------


def _hist(tuning, holdout=None):
    holdout = holdout or [70.0] * len(tuning)
    return [
        {
            "iteration": i,
            "label": "baseline" if i == 0 else f"plan {i:02d}",
            "tuning": {"n": 1000, "correct": round(t * 10), "accuracy": t / 100},
            "holdout": {"n": 1000, "correct": round(h * 10), "accuracy": h / 100},
        }
        for i, (t, h) in enumerate(zip(tuning, holdout, strict=True))
    ]


@pytest.mark.parametrize(
    "tuning, holdout, reached, reason",
    [
        ([60.0, 69.2, 70.0], None, False, "2 tuning plan(s) applied"),
        ([60.0, 69.2, 70.0, 70.4], None, True, "gained < 1.0 pp"),
        ([60.0, 69.2, 70.0, 70.4], [65.0, 70.0, 68.0, 67.5], False, "holdout accuracy is 2.5 pp below its best"),
        ([60.0, 68.0, 70.0, 72.0], None, False, "still improving"),
        ([80.0, 90.0, 95.0, 100.0], None, True, "reached 100%"),
        ([60.0, 69.2, 70.0, 70.4], [65.0, 70.0, 68.0, 68.0], True, "holdout within 2.0 pp"),
    ],
)
def test_asymptote_rule(tuning, holdout, reached, reason):
    state = asymptote(_hist(tuning, holdout))
    assert state["reached"] is reached and reason in state["reason"], state
    assert state["fix_iterations"] == len(tuning) - 1 and not state["exhausted"]


def test_asymptote_reports_deltas_gap_and_exhaustion():
    state = asymptote(list(reversed(_hist([60.0, 69.2, 70.0, 70.4]))))  # order of entries does not matter
    assert state["last_deltas_pp"] == [0.8, 0.4] and state["holdout_gap_pp"] == 0.0
    state = asymptote(_hist([50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0]))
    assert not state["reached"] and state["exhausted"] and "6 tuning plans applied" in state["reason"]
    assert asymptote([])["reached"] is False


def test_append_history_and_history_entry(tmp_path):
    path = tmp_path / "tuning" / "accuracy_history.json"
    s = score(
        [
            Result("a", "a", matches_expected=True, split="tuning"),
            Result("b", "b", matches_expected=False, split="holdout"),
        ]
    )
    entry = history_entry(0, "baseline", s, eval_run_id="run0", started_at="2026-11-25T00:00:00+00:00")
    assert entry["tuning"] == {"n": 1, "correct": 1, "accuracy": 1.0} and entry["changes"] == []
    assert append_history(path, entry) == [entry]
    second = history_entry(1, "plan 01", s, changes=["mv_orders: comment"])
    hist = append_history(path, second)
    assert [h["iteration"] for h in hist] == [0, 1] and json.loads(path.read_text()) == hist
    with pytest.raises(ValueError, match="already recorded"):
        append_history(path, entry)
    with pytest.raises(ValueError, match="missing"):
        append_history(path, {"iteration": 5})


def test_write_iteration_md_lists_only_tuning_failures(tmp_path):
    hist = _hist([60.0, 69.2, 70.0, 70.4])
    entry = dict(hist[-1], eval_run_id="run3", changes=["mv_orders.Return Rate: format percentage"])
    results = [
        Result("t1", "tuning miss | pipe", matches_expected=False, split="tuning", unit_mismatch=True),
        Result("t2", "tuning hit", matches_expected=True, split="tuning"),
        Result("h1", "holdout miss", matches_expected=False, split="holdout"),
    ]
    out = write_iteration_md(
        tmp_path / "iterations" / "3.md",
        entry,
        state=asymptote(hist),
        results=results,
        plan_applied="tuning_plan_03.md",
        next_plan="tuning_plan_04.md",
    )
    text = out.read_text()
    assert text.startswith("# Tuning iteration 3: plan 03")
    assert "| Tuning accuracy | 70.4% (704/1000) |" in text and "| Asymptote reached | yes |" in text
    assert "| Plan applied | tuning_plan_03.md |" in text and "* mv_orders.Return Rate: format percentage" in text
    assert "| t1 | tuning miss \\| pipe |" in text and "t2" not in text
    assert "h1" not in text and "holdout miss" not in text


def test_write_results_md_has_split_and_unit_columns(tmp_path):
    results = [
        Result(
            "a", "a", sql_generated=True, sql_succeeded=True, matches_expected=False, split="tuning", unit_mismatch=True
        )
    ]
    text = write_results_md(score(results), results, tmp_path / "r.md").read_text()
    assert "| Unit mismatches | 1 |" in text and "| Tuning accuracy | 0.0% (0/1) |" in text
    header = next(line for line in text.splitlines() if line.startswith("| ID |"))
    row = next(line for line in text.splitlines() if line.startswith("| a |"))
    assert "Split" in header and "Unit mismatch" in header and header.count("|") == row.count("|")
