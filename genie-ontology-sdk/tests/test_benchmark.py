"""Tests for genie_ontology_sdk.benchmark (fake Genie client, no live API calls)."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace as NS

import pytest

import genie_ontology_sdk.benchmark as bm
from genie_ontology_sdk.benchmark import (
    ACCURACY_GATE,
    Question,
    Result,
    load_questions,
    run_benchmark,
    score,
    write_results_md,
)

QUESTIONS = Path(__file__).parent / "fixtures" / "benchmark" / "questions.yml"
SPACE = "space-1"


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

    def start_conversation_and_wait(self, space_id, content, *, timeout=None, **_):
        self.calls.append(("start", space_id, content, timeout))
        a = self.answers[content]
        if "raise" in a:
            raise a["raise"]
        n = len(self.calls)
        atts = []
        if a.get("text"):
            atts.append(NS(attachment_id=f"t{n}", text=NS(content=a["text"]), query=None))
        if "sql" in a:
            atts.append(NS(attachment_id=f"a{n}", text=None, query=NS(query=a["sql"])))
            self._results[f"a{n}"] = _stmt(a.get("rows", []), state=a.get("state", "SUCCEEDED"), error=a.get("error"))
        return NS(conversation_id=f"c{n}", message_id=f"m{n}", id=f"m{n}",
                  status=NS(value="COMPLETED"), error=None, attachments=atts)

    def get_message_attachment_query_result(self, space_id, conversation_id, message_id, attachment_id):
        self.calls.append(("result", space_id, conversation_id, message_id, attachment_id))
        return NS(statement_response=self._results[attachment_id])


class FakeStatements:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def execute_statement(self, statement, warehouse_id, **kw):
        self.calls.append((statement, warehouse_id, kw))
        return _stmt(self.rows)


def _ws(answers, expected_rows=None):
    return NS(genie=FakeGenie(answers), statement_execution=FakeStatements(expected_rows or []))


@pytest.fixture
def questions():
    return load_questions(QUESTIONS)


GOOD_ANSWERS = {
    "What is total net revenue?": {"sql": "SELECT SUM(x) FROM t", "rows": [["1000.50"]]},
    "How many orders are there per order priority?": {
        "sql": "SELECT p, COUNT(*) FROM o GROUP BY p", "rows": [["2-HIGH", "2"], ["1-urgent", "3"]],
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


@pytest.mark.parametrize("text, message", [
    ("- id: a\n  question: x\n- id: a\n  question: y\n", "duplicate id"),
    ("- question: x\n", "missing 'id'"),
    ("- id: a\n  question: ''\n", "empty question"),
    ("- id: a\n  question: x\n  answer: 1\n", "unknown keys"),
    ("id: a\n", "expected a YAML list"),
])
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
        "sql": "SELECT bad", "state": "FAILED", "error": "UNRESOLVED_COLUMN",
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
    return Result(question_id=qid, question=qid, sql_generated=gen, sql_succeeded=ok,
                  matches_expected=match, error=error)


def test_score_accuracy_uses_expectations_when_present():
    s = score([
        _r("a", True, True, True),
        _r("b", True, True, False),
        _r("c", True, True, True),
        _r("d", True, False, False, error="x"),
        _r("e", True, True, None),
        _r("f", False, False, None),
    ])
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
    for phrase in ("Scoring definition", "accuracy", "with_expectations", "sql_succeeded / total", "0.70"):
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
