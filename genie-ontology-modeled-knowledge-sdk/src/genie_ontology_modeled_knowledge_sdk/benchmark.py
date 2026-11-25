"""Genie Agent benchmark: ask questions, capture SQL and results, score them.

Used by the tuning wave (L200-H Phase 3: 10-20 benchmark questions per
agent). Questions live in ``docs/tuning/benchmark_questions.yml``::

    - id: q01
      question: What was total net revenue in 1995?
      expected_sql: SELECT ...        # optional
      expected_answer: 1234.56        # optional: scalar or list of rows
      tags: [revenue]

Public API:

* ``load_questions(path) -> list[Question]``
* ``run_benchmark(space_id, questions, ws, *, timeout_s=120, warehouse_id=None) -> list[Result]``
* ``score(results) -> Summary``
* ``write_results_md(summary, results, path)``

Scoring definition
------------------

Each question is asked once, in its own Genie conversation
(``ws.genie.start_conversation_and_wait``). Per result:

* **sql_generated**: the answer has a query attachment with non-empty SQL.
* **sql_succeeded**: SQL was generated and its query result
  (``ws.genie.get_message_attachment_query_result``) has statement state
  ``SUCCEEDED``.
* **matches_expected**: ``None`` when the question has no expectation, or has
  only ``expected_sql`` and no ``warehouse_id`` was given (not evaluated).
  Otherwise ``False`` unless the SQL succeeded and:

  * ``expected_answer`` is a scalar: some cell of the first result row equals
    it;
  * ``expected_answer`` is a list: the result rows equal the expected rows as a
    multiset (row order ignored; a scalar list item is a one-column row);
  * ``expected_sql`` (evaluated on ``warehouse_id``): the result rows equal the
    expected query's rows as a multiset.

  When both are given, ``expected_answer`` is used. Values are compared after
  normalization: numbers with relative tolerance 1e-4 (absolute 1e-6), other
  values as trimmed, case-insensitive strings, ``NULL`` as ``None``.

Summary counts: ``total``, ``sql_generated``, ``sql_succeeded``,
``with_expectations`` (results whose ``matches_expected`` is not ``None``),
``matches_expected``, ``errors``.

**accuracy** = ``matches_expected / with_expectations`` when
``with_expectations > 0`` (``accuracy_basis = "expected"``), else
``sql_succeeded / total`` (``accuracy_basis = "succeeded"``); 0.0 for an empty
run. The tuning gate is ``accuracy >= 0.70`` (``ACCURACY_GATE``).

L200-H also scores *correct interpretation*; that needs a person or a judge,
so ``write_results_md`` leaves an empty ``Interpretation`` column for review.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from collections import Counter
from datetime import timedelta
from pathlib import Path
from typing import Any, Iterable

import yaml

__all__ = [
    "ACCURACY_GATE",
    "Question",
    "Result",
    "Summary",
    "load_questions",
    "run_benchmark",
    "score",
    "write_results_md",
]

ACCURACY_GATE = 0.70
REL_TOL = 1e-4
ABS_TOL = 1e-6


@dataclass
class Question:
    id: str
    question: str
    expected_sql: str | None = None
    expected_answer: Any = None
    tags: list[str] = field(default_factory=list)

    @property
    def has_expectation(self) -> bool:
        return self.expected_answer is not None or bool(self.expected_sql)


@dataclass
class Result:
    question_id: str
    question: str
    status: str | None = None
    conversation_id: str | None = None
    message_id: str | None = None
    sql: str | None = None
    sql_generated: bool = False
    sql_succeeded: bool = False
    columns: list[str] = field(default_factory=list)
    rows: list[list[Any]] = field(default_factory=list)
    text: str | None = None
    matches_expected: bool | None = None
    error: str | None = None
    elapsed_s: float = 0.0
    tags: list[str] = field(default_factory=list)


@dataclass
class Summary:
    total: int = 0
    sql_generated: int = 0
    sql_succeeded: int = 0
    with_expectations: int = 0
    matches_expected: int = 0
    errors: int = 0
    accuracy: float = 0.0
    accuracy_basis: str = "succeeded"

    @property
    def passes_gate(self) -> bool:
        return self.accuracy >= ACCURACY_GATE


# ---------------------------------------------------------------------------
# Questions
# ---------------------------------------------------------------------------


def load_questions(path: str | Path) -> list[Question]:
    """Load a YAML list of ``{id, question, expected_sql?, expected_answer?, tags}``.

    A top-level mapping with a ``questions`` list is also accepted. Raises
    ``ValueError`` for a missing/duplicate ``id``, an empty ``question``, or
    unknown keys.
    """
    p = Path(path)
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "questions" in data:
        data = data["questions"]
    if not isinstance(data, list):
        raise ValueError(f"{p}: expected a YAML list of questions")
    allowed = {"id", "question", "expected_sql", "expected_answer", "tags"}
    out: list[Question] = []
    seen: set[str] = set()
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"{p}: item {i} must be a mapping")
        unknown = set(item) - allowed
        if unknown:
            raise ValueError(f"{p}: item {i} has unknown keys {sorted(unknown)}")
        qid = str(item.get("id") or "").strip()
        text = str(item.get("question") or "").strip()
        if not qid:
            raise ValueError(f"{p}: item {i} is missing 'id'")
        if qid in seen:
            raise ValueError(f"{p}: duplicate id '{qid}'")
        if not text:
            raise ValueError(f"{p}: '{qid}' has an empty question")
        tags = item.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]
        seen.add(qid)
        out.append(Question(
            id=qid,
            question=text,
            expected_sql=(str(item["expected_sql"]).strip() or None) if item.get("expected_sql") else None,
            expected_answer=item.get("expected_answer"),
            tags=[str(t) for t in tags],
        ))
    return out


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------


def _norm(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if s.upper() == "NULL" or s == "":
        return None if s.upper() == "NULL" else ""
    try:
        return float(s.replace(",", "")) if any(c.isdigit() for c in s) else s.casefold()
    except ValueError:
        return s.casefold()


def _eq(a: Any, b: Any) -> bool:
    a, b = _norm(a), _norm(b)
    if isinstance(a, float) and isinstance(b, float):
        return math.isclose(a, b, rel_tol=REL_TOL, abs_tol=ABS_TOL)
    return a == b


def _rows_equal(actual: list[list[Any]], expected: list[list[Any]]) -> bool:
    """Multiset row equality with tolerant cell comparison."""
    if len(actual) != len(expected):
        return False
    remaining = list(actual)
    for exp in expected:
        for i, act in enumerate(remaining):
            if len(act) == len(exp) and all(_eq(x, y) for x, y in zip(act, exp)):
                del remaining[i]
                break
        else:
            return False
    return True


def _as_rows(expected: list[Any]) -> list[list[Any]]:
    return [list(r) if isinstance(r, (list, tuple)) else [r] for r in expected]


def _match_answer(rows: list[list[Any]], expected: Any) -> bool:
    if isinstance(expected, (list, tuple)):
        return _rows_equal(rows, _as_rows(list(expected)))
    return bool(rows) and any(_eq(cell, expected) for cell in rows[0])


# ---------------------------------------------------------------------------
# Running
# ---------------------------------------------------------------------------


def _state(statement_response: Any) -> str | None:
    status = getattr(statement_response, "status", None)
    state = getattr(status, "state", None)
    return getattr(state, "value", state) if state is not None else None


def _rows_and_columns(statement_response: Any) -> tuple[list[str], list[list[Any]]]:
    manifest = getattr(statement_response, "manifest", None)
    schema = getattr(manifest, "schema", None)
    columns = [c.name for c in (getattr(schema, "columns", None) or [])]
    result = getattr(statement_response, "result", None)
    rows = [list(r) for r in (getattr(result, "data_array", None) or [])]
    return columns, rows


def _statement_error(statement_response: Any) -> str | None:
    err = getattr(getattr(statement_response, "status", None), "error", None)
    return getattr(err, "message", None) or (str(err) if err else None)


def _run_expected_sql(ws: Any, warehouse_id: str, sql: str, timeout_s: int) -> list[list[Any]]:
    resp = ws.statement_execution.execute_statement(
        statement=sql, warehouse_id=warehouse_id, wait_timeout=f"{min(max(timeout_s, 5), 50)}s",
    )
    if _state(resp) != "SUCCEEDED":
        raise RuntimeError(f"expected_sql did not succeed ({_state(resp)}): {_statement_error(resp)}")
    return _rows_and_columns(resp)[1]


def _ask(space_id: str, q: Question, ws: Any, timeout_s: int, warehouse_id: str | None) -> Result:
    r = Result(question_id=q.id, question=q.question, tags=list(q.tags))
    start = time.monotonic()
    try:
        msg = ws.genie.start_conversation_and_wait(space_id, q.question, timeout=timedelta(seconds=timeout_s))
        r.conversation_id = getattr(msg, "conversation_id", None)
        r.message_id = getattr(msg, "message_id", None) or getattr(msg, "id", None)
        status = getattr(msg, "status", None)
        r.status = getattr(status, "value", status)
        msg_error = getattr(msg, "error", None)
        if msg_error:
            r.error = getattr(msg_error, "error", None) or str(msg_error)

        texts = []
        for att in getattr(msg, "attachments", None) or []:
            text = getattr(att, "text", None)
            if text is not None and getattr(text, "content", None):
                texts.append(text.content)
            query = getattr(att, "query", None)
            if query is None or r.sql_generated:
                continue
            sql = (getattr(query, "query", None) or "").strip()
            if not sql:
                continue
            r.sql, r.sql_generated = sql, True
            qr = ws.genie.get_message_attachment_query_result(
                space_id, r.conversation_id, r.message_id, att.attachment_id,
            )
            stmt = getattr(qr, "statement_response", None)
            if _state(stmt) == "SUCCEEDED":
                r.sql_succeeded = True
                r.columns, r.rows = _rows_and_columns(stmt)
            else:
                r.error = r.error or f"query state {_state(stmt)}: {_statement_error(stmt)}"
        r.text = "\n\n".join(texts) or None

        if q.expected_answer is not None:
            r.matches_expected = r.sql_succeeded and _match_answer(r.rows, q.expected_answer)
        elif q.expected_sql and warehouse_id:
            r.matches_expected = r.sql_succeeded and _rows_equal(
                r.rows, _run_expected_sql(ws, warehouse_id, q.expected_sql, timeout_s),
            )
    except Exception as e:  # noqa: BLE001 - recorded on the result; one failing question must not stop the run
        r.error = f"{type(e).__name__}: {e}"
        if q.expected_answer is not None or (q.expected_sql and warehouse_id):
            r.matches_expected = bool(r.matches_expected)
    r.elapsed_s = round(time.monotonic() - start, 3)
    return r


def run_benchmark(
    space_id: str,
    questions: Iterable[Question],
    ws: Any,
    *,
    timeout_s: int = 120,
    warehouse_id: str | None = None,
) -> list[Result]:
    """Ask each question in a new conversation and capture SQL + result.

    ``ws`` is a ``databricks.sdk.WorkspaceClient`` (uses ``ws.genie`` and, for
    ``expected_sql`` with ``warehouse_id``, ``ws.statement_execution``).
    Errors and timeouts are recorded on the ``Result`` (``error``) and the run
    continues. Only the first chunk of each query result is read.
    """
    return [_ask(space_id, q, ws, timeout_s, warehouse_id) for q in questions]


# ---------------------------------------------------------------------------
# Scoring and reporting
# ---------------------------------------------------------------------------


def score(results: Iterable[Result]) -> Summary:
    """Summarize results; see the module docstring for the definition."""
    results = list(results)
    s = Summary(total=len(results))
    s.sql_generated = sum(r.sql_generated for r in results)
    s.sql_succeeded = sum(r.sql_succeeded for r in results)
    s.with_expectations = sum(r.matches_expected is not None for r in results)
    s.matches_expected = sum(r.matches_expected is True for r in results)
    s.errors = sum(r.error is not None for r in results)
    if s.with_expectations:
        s.accuracy, s.accuracy_basis = s.matches_expected / s.with_expectations, "expected"
    elif s.total:
        s.accuracy, s.accuracy_basis = s.sql_succeeded / s.total, "succeeded"
    return s


def _cell(value: Any, limit: int = 120) -> str:
    text = "" if value is None else " ".join(str(value).split())
    if len(text) > limit:
        text = text[: limit - 3] + "..."
    return text.replace("|", "\\|")


def _yn(value: bool | None) -> str:
    return "n/a" if value is None else ("yes" if value else "no")


def write_results_md(summary: Summary, results: Iterable[Result], path: str | Path) -> Path:
    """Write a markdown report (summary, per-question table, SQL details)."""
    results = list(results)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    gate = "pass" if summary.passes_gate else "fail"
    lines = [
        "# Benchmark results",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Questions | {summary.total} |",
        f"| SQL generated | {summary.sql_generated} |",
        f"| SQL succeeded | {summary.sql_succeeded} |",
        f"| With expectations | {summary.with_expectations} |",
        f"| Matches expected | {summary.matches_expected} |",
        f"| Errors | {summary.errors} |",
        f"| Accuracy | {summary.accuracy:.1%} ({summary.accuracy_basis}) |",
        f"| Gate (>= {ACCURACY_GATE:.0%}) | {gate} |",
        "",
        "## Questions",
        "",
        "| ID | Question | SQL generated | SQL succeeded | Matches expected | Interpretation | Tags | Error |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {_cell(r.question_id)} | {_cell(r.question)} | {_yn(r.sql_generated)} | {_yn(r.sql_succeeded)} "
            f"| {_yn(r.matches_expected)} |  | {_cell(', '.join(r.tags))} | {_cell(r.error)} |"
        )
    lines += ["", "## SQL", ""]
    for r in results:
        lines += [f"### {r.question_id}", "", r.question, ""]
        if r.sql:
            lines += ["```sql", r.sql, "```", ""]
        else:
            lines += ["_No SQL generated._", ""]
        if r.sql_succeeded:
            lines += [f"Rows returned: {len(r.rows)}", ""]
    p.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return p
