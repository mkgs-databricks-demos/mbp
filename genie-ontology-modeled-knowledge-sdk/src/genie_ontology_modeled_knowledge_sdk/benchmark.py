"""Genie Agent benchmark: question sets, coverage, splits, evaluation and scoring.

Used by the exhaustive tuning protocol (``docs/plans/build-1/INDEX.md``,
``skills/ontology-tuning``): 100-498 questions per agent covering every metric
view, a deterministic holdout split, Genie benchmark evaluation runs, an
accuracy history per tuning iteration and the asymptote stop rule. Questions
live in one folder per agent (``docs/tuning/benchmark/*.yml``, ids prefixed by
file)::

    - id: s001
      question: What was total net revenue in 1995?
      expected_sql: SELECT MEASURE(`Net Revenue`) FROM ${target_catalog}...
      expected_answer: 1234.56        # optional: scalar or list of rows
      tags: [type:simple, view:mv_sales, measure:Net Revenue, dimension:Order Year]
      split: holdout                  # optional; default from assign_splits

Tags of the form ``type:<t>``, ``view:<mv>``, ``measure:<m>`` (or
``measure:<mv>.<m>``) and ``dimension:<d>`` (or ``dimension:<mv>.<d>``) are
parsed into ``Question.type``, ``views``, ``measures`` and ``dimensions``;
other tags are kept as free labels. Types: ``QUESTION_TYPES``.

Public API:

* ``load_questions(path) -> list[Question]`` (one file),
  ``load_question_set(folder) -> list[Question]`` (every ``*.yml``/``*.yaml``,
  ids unique across files)
* ``coverage(questions, mv_yaml_paths) -> CoverageReport``; CLI
  ``python -m genie_ontology_modeled_knowledge_sdk.benchmark coverage
  <questions_dir> <metric_views_dir>`` exits 1 on problems
* ``assign_splits(questions, holdout=HOLDOUT_SHARE) -> {id: split}``
* ``to_space_benchmarks(questions) -> {"questions": [...]}``,
  ``benchmark_id(question_id)``
* ``run_eval(space_id, ws, question_ids=None, poll_s=10, timeout_s=7200,
  questions=None) -> EvalRun``
* ``run_benchmark(space_id, questions, ws, *, timeout_s=120,
  warehouse_id=None, max_workers=4) -> list[Result]`` (fallback)
* ``score(results, splits=None) -> Summary``
* ``write_results_md(summary, results, path)``
* ``history_entry(...)``, ``append_history(path, entry)``,
  ``asymptote(history) -> dict``, ``write_iteration_md(path, entry, ...)``

Coverage rules
--------------

``coverage`` reports a problem when: fewer than ``MIN_QUESTIONS`` (100) or
more than ``MAX_QUESTIONS`` (498) questions; a metric view has fewer than
``MIN_PER_VIEW`` (12) questions; a measure or dimension of a metric view is
never tagged; fewer than ``MIN_CROSS_VIEW_SHARE`` (25%) of the questions are
tagged with two or more views; a type in ``QUESTION_TYPES`` is unused; a
question has no ``type:`` tag, an unknown type, view, measure or dimension, or
no ``expected_sql``. Metric view names are the YAML file stems; measures come
from ``measures``, dimensions from ``dimensions`` and ``fields``. An
unqualified ``measure:``/``dimension:`` tag credits every view of the question
that has it (every view, when the question has no ``view:`` tag).

Splits
------

``assign_splits`` puts a question in ``holdout`` when the first 8 bytes of
``sha256(id)`` read as a fraction of 2**64 are below ``holdout`` (0.2), else in
``tuning``; an explicit ``split:`` in the YAML wins. The split depends only on
the id, so it is stable across runs and machines. Tuning sessions read only
``tuning`` failures (``write_iteration_md`` never lists holdout failures).

Scoring definition
------------------

Each fallback question (``run_benchmark``) is asked once, in its own Genie
conversation (``ws.genie.start_conversation_and_wait``), at most
``max_workers`` at a time; HTTP 429 and 5xx responses are retried with
exponential backoff (``_with_backoff``). Per result:

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
* **unit_mismatch**: the result is not a match, but would be if the expected
  ratio were multiplied by 100 or divided by 100 (a 0-1 ratio returned as a
  percentage, or the reverse). Ratio expectations are: a scalar of a
  ``type:ratio`` question or any non-integral scalar; for row expectations, the
  non-integral numeric cells. A unit mismatch still counts as a miss.
* **needs_review** (evaluation runs only): Genie could not grade the answer;
  it counts as not matched and is listed in ``EvalRun.needs_review``.

Summary counts: ``total``, ``sql_generated``, ``sql_succeeded``,
``with_expectations`` (results whose ``matches_expected`` is not ``None``),
``matches_expected``, ``errors``, ``unit_mismatch``, ``needs_review``.

**accuracy** = ``matches_expected / with_expectations`` when
``with_expectations > 0`` (``accuracy_basis = "expected"``), else
``sql_succeeded / total`` (``accuracy_basis = "succeeded"``); 0.0 for an empty
run. The tuning gate is ``accuracy >= 0.70`` (``ACCURACY_GATE``). Per split,
``Summary.tuning`` and ``Summary.holdout`` are ``{n, correct, accuracy}`` over
the results with expectations in that split (``accuracy`` 0.0 when ``n`` is 0).

L200-H also scores *correct interpretation*; that needs a person or a judge,
so ``write_results_md`` leaves an empty ``Interpretation`` column for review.

Genie benchmark evaluation runs
-------------------------------

``to_space_benchmarks`` returns the serialized-space ``benchmarks`` section
that ``geniespace.build_space(..., benchmarks=...)`` accepts::

    {"questions": [{"id": benchmark_id(q.id), "question": [q.question],
                    "answer": [{"format": "SQL", "content": [<sql lines>]}]}]}

(shape from the Genie Agents API docs, which require exactly one ``SQL``
answer per benchmark question; not verified on an exported space because the
build-0 TPC-H agent has no benchmarks). ``expected_sql`` stays tokenized; the
render step resolves it. Every question needs ``expected_sql``; at most
``MAX_SPACE_BENCHMARKS`` (500) questions. ``benchmark_id`` is a stable
32-character hex id (uuid5 of the question id), so Genie results map back to
question ids.

``run_eval`` calls the eval-runs REST API through ``ws.api_client.do`` (the
SDK floor 0.45 has no wrapper): ``POST /api/2.0/genie/spaces/{id}/eval-runs``
(``benchmark_question_ids`` = ``benchmark_id`` of the given question ids, or
all), polls ``GET .../eval-runs/{run}`` with growing intervals until
``eval_run_status`` leaves ``NOT_STARTED``/``RUNNING``, then pages
``GET .../eval-runs/{run}/results`` (100 per page) and reads
``GET .../results/{result_id}`` for each. Per result: ``assessment`` is the verdict
(a reviewer's edit in the UI updates it; ``manual_assessment`` is only a
flag saying whether that happened, never a verdict); ``GOOD`` is a match,
``BAD`` a miss, ``NEEDS_REVIEW`` or no assessment a miss with
``needs_review``. The ``SQL`` actual response gives ``sql``; its
``sql_execution_result`` gives ``sql_succeeded``, columns and rows (and
``unit_mismatch`` against the expected response's rows). A run that ends in
any status other than ``DONE`` raises ``RuntimeError``.

Stop rule (asymptote)
---------------------

``accuracy_history.json`` is a list of ``{iteration, label, eval_run_id,
started_at, tuning: {n, correct, accuracy}, holdout: {...}, changes}``;
iteration 0 is the baseline, iterations >= 1 are applied tuning plans.
``asymptote(history)`` is reached when at least ``MIN_FIX_ITERATIONS`` (3)
plans were applied, **and** the tuning-split accuracy gained less than
``ASYMPTOTE_DELTA_PP`` (1.0) percentage points in each of the last
``ASYMPTOTE_WINDOW`` (2) iterations or is 100%, **and** the latest holdout
accuracy is within ``HOLDOUT_TOLERANCE_PP`` (2.0) points of its best. When it
is not reached after ``MAX_FIX_ITERATIONS`` (6), ``exhausted`` is true.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
import time
import uuid
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, TypeVar

import yaml

from . import mv_yaml

__all__ = [
    "ACCURACY_GATE",
    "ASYMPTOTE_DELTA_PP",
    "ASYMPTOTE_WINDOW",
    "HOLDOUT_SHARE",
    "HOLDOUT_TOLERANCE_PP",
    "MAX_FIX_ITERATIONS",
    "MAX_QUESTIONS",
    "MAX_SPACE_BENCHMARKS",
    "MIN_CROSS_VIEW_SHARE",
    "MIN_FIX_ITERATIONS",
    "MIN_PER_VIEW",
    "MIN_QUESTIONS",
    "QUESTION_TYPES",
    "SPLITS",
    "CoverageReport",
    "EvalRun",
    "Question",
    "Result",
    "Summary",
    "append_history",
    "assign_splits",
    "asymptote",
    "benchmark_id",
    "coverage",
    "history_entry",
    "load_question_set",
    "load_questions",
    "main",
    "run_benchmark",
    "run_eval",
    "score",
    "to_space_benchmarks",
    "write_iteration_md",
    "write_results_md",
]

ACCURACY_GATE = 0.70
REL_TOL = 1e-4
ABS_TOL = 1e-6

#: Exhaustive tuning protocol constants (docs/plans/build-1/INDEX.md).
MIN_QUESTIONS = 100
MAX_QUESTIONS = 498
MIN_PER_VIEW = 12
MIN_CROSS_VIEW_SHARE = 0.25
HOLDOUT_SHARE = 0.2
MIN_FIX_ITERATIONS = 3
ASYMPTOTE_DELTA_PP = 1.0
ASYMPTOTE_WINDOW = 2
HOLDOUT_TOLERANCE_PP = 2.0
MAX_FIX_ITERATIONS = 6
#: Genie allows up to 500 benchmark questions per agent.
MAX_SPACE_BENCHMARKS = 500

QUESTION_TYPES = ("simple", "breakdown", "time", "filter", "ratio", "synonym", "edge", "cross_view")
SPLITS = ("tuning", "holdout")
UNIT_FACTORS = (100.0, 0.01)

#: Retry policy for Genie API calls (HTTP 429 / 5xx).
RETRY_STATUS = frozenset({429, 500, 502, 503, 504})
MAX_RETRIES = 6
BACKOFF_BASE_S = 2.0
BACKOFF_MAX_S = 60.0
POLL_MAX_S = 60.0
EVAL_PAGE_SIZE = 100
EVAL_RUNNING = ("NOT_STARTED", "RUNNING")

_BENCHMARK_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "genie-ontology-modeled-knowledge-sdk/benchmark")
_TAG_KEYS = ("type", "view", "measure", "dimension")

# Indirection so tests can run without real sleeps or jitter.
_sleep = time.sleep
_jitter = random.random

T = TypeVar("T")


@dataclass
class Question:
    id: str
    question: str
    expected_sql: str | None = None
    expected_answer: Any = None
    tags: list[str] = field(default_factory=list)
    split: str | None = None

    @property
    def has_expectation(self) -> bool:
        return self.expected_answer is not None or bool(self.expected_sql)

    def _tag_values(self, key: str) -> list[str]:
        out: list[str] = []
        for tag in self.tags:
            k, sep, value = tag.partition(":")
            if sep and k.strip().lower() == key and value.strip() and value.strip() not in out:
                out.append(value.strip())
        return out

    @property
    def type(self) -> str | None:
        values = self._tag_values("type")
        return values[0] if values else None

    @property
    def views(self) -> list[str]:
        return self._tag_values("view")

    @property
    def measures(self) -> list[str]:
        return self._tag_values("measure")

    @property
    def dimensions(self) -> list[str]:
        return self._tag_values("dimension")


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
    split: str | None = None
    unit_mismatch: bool = False
    needs_review: bool = False
    assessment: str | None = None


def _split_block(n: int = 0, correct: int = 0) -> dict[str, Any]:
    return {"n": n, "correct": correct, "accuracy": (correct / n) if n else 0.0}


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
    unit_mismatch: int = 0
    needs_review: int = 0
    tuning: dict[str, Any] = field(default_factory=_split_block)
    holdout: dict[str, Any] = field(default_factory=_split_block)

    @property
    def passes_gate(self) -> bool:
        return self.accuracy >= ACCURACY_GATE


# ---------------------------------------------------------------------------
# Questions
# ---------------------------------------------------------------------------


def load_questions(path: str | Path) -> list[Question]:
    """Load a YAML list of ``{id, question, expected_sql?, expected_answer?, tags, split?}``.

    A top-level mapping with a ``questions`` list is also accepted. Raises
    ``ValueError`` for a missing/duplicate ``id``, an empty ``question``,
    unknown keys, or a ``split`` other than ``tuning``/``holdout``.
    """
    p = Path(path)
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "questions" in data:
        data = data["questions"]
    if not isinstance(data, list):
        raise ValueError(f"{p}: expected a YAML list of questions")
    allowed = {"id", "question", "expected_sql", "expected_answer", "tags", "split"}
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
        split = item.get("split")
        if split is not None:
            split = str(split).strip().lower()
            if split not in SPLITS:
                raise ValueError(f"{p}: '{qid}' has split {item.get('split')!r}; expected one of {list(SPLITS)}")
        seen.add(qid)
        out.append(
            Question(
                id=qid,
                question=text,
                expected_sql=(str(item["expected_sql"]).strip() or None) if item.get("expected_sql") else None,
                expected_answer=item.get("expected_answer"),
                tags=[str(t) for t in tags],
                split=split,
            )
        )
    return out


def load_question_set(folder: str | Path) -> list[Question]:
    """Load every ``*.yml`` / ``*.yaml`` file in ``folder`` (sorted by name, not recursive).

    Raises ``ValueError`` when the folder has no question files or an id
    appears in more than one file.
    """
    root = Path(folder)
    if not root.is_dir():
        raise ValueError(f"{root}: not a folder")
    files = sorted(p for p in root.iterdir() if p.is_file() and p.suffix.lower() in (".yml", ".yaml"))
    if not files:
        raise ValueError(f"{root}: no *.yml question files")
    out: list[Question] = []
    first_file: dict[str, Path] = {}
    for f in files:
        for q in load_questions(f):
            if q.id in first_file:
                raise ValueError(f"{f}: duplicate id '{q.id}' (also in {first_file[q.id].name})")
            first_file[q.id] = f
            out.append(q)
    return out


# ---------------------------------------------------------------------------
# Coverage
# ---------------------------------------------------------------------------


@dataclass
class CoverageReport:
    """Coverage of a question set against metric views; see the module docstring."""

    total: int = 0
    per_view: dict[str, int] = field(default_factory=dict)
    per_measure: dict[str, int] = field(default_factory=dict)
    per_dimension: dict[str, int] = field(default_factory=dict)
    cross_view: int = 0
    cross_view_share: float = 0.0
    type_mix: dict[str, int] = field(default_factory=dict)
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["ok"] = self.ok
        return d

    def to_text(self) -> str:
        lines = [
            f"questions: {self.total}",
            f"cross-view: {self.cross_view} ({self.cross_view_share:.1%})",
            "types: " + ", ".join(f"{k}={v}" for k, v in sorted(self.type_mix.items())),
            "per view:",
        ]
        lines += [f"  {v}: {n}" for v, n in sorted(self.per_view.items())]
        lines.append("coverage: ok" if self.ok else f"coverage: {len(self.problems)} problem(s)")
        lines += [f"  PROBLEM: {p}" for p in self.problems]
        return "\n".join(lines)


def _columns(entries: Any) -> list[str]:
    out: list[str] = []
    for e in entries or []:
        if isinstance(e, Mapping) and e.get("name"):
            out.append(str(e["name"]))
    return out


def _load_views(mv_yaml_paths: str | Path | Iterable[str | Path]) -> dict[str, dict[str, list[str]]]:
    roots = [mv_yaml_paths] if isinstance(mv_yaml_paths, (str, Path)) else list(mv_yaml_paths)
    views: dict[str, dict[str, list[str]]] = {}
    for root in roots:
        for f in mv_yaml.iter_mv_files(root):
            doc = mv_yaml.load_mv(f)
            if f.stem in views:
                raise ValueError(f"{f}: duplicate metric view name '{f.stem}'")
            views[f.stem] = {
                "measures": _columns(doc.get("measures")),
                "dimensions": _columns(doc.get("dimensions")) + _columns(doc.get("fields")),
            }
    if not views:
        raise ValueError(f"no metric view YAML files under {roots}")
    return views


def _ids(ids: Sequence[str], limit: int = 10) -> str:
    shown = ", ".join(ids[:limit])
    return shown + (f", ... (+{len(ids) - limit})" if len(ids) > limit else "")


def coverage(questions: Iterable[Question], mv_yaml_paths: str | Path | Iterable[str | Path]) -> CoverageReport:
    """Count questions per metric view, measure, dimension and type; list problems.

    ``mv_yaml_paths`` is a metric view YAML file or folder, or a list of them.
    """
    qs = list(questions)
    views = _load_views(mv_yaml_paths)
    by_fold = {v.casefold(): v for v in views}
    cols: dict[str, dict[str, dict[str, str]]] = {
        kind: {v: {c.casefold(): c for c in views[v][kind]} for v in views} for kind in ("measures", "dimensions")
    }
    rep = CoverageReport(total=len(qs))
    rep.per_view = {v: 0 for v in sorted(views)}
    rep.per_measure = {f"{v}.{m}": 0 for v in sorted(views) for m in views[v]["measures"]}
    rep.per_dimension = {f"{v}.{d}": 0 for v in sorted(views) for d in views[v]["dimensions"]}
    counters = {"measures": rep.per_measure, "dimensions": rep.per_dimension}
    types: Counter[str] = Counter()
    no_type: list[str] = []
    no_sql: list[str] = []
    unknown: dict[str, list[str]] = {"type": [], "view": [], "measures": [], "dimensions": []}

    for q in qs:
        qviews: list[str] = []
        for v in q.views:
            name = by_fold.get(v.casefold())
            if name is None:
                unknown["view"].append(f"{q.id}:{v}")
            elif name not in qviews:
                qviews.append(name)
        for v in qviews:
            rep.per_view[v] += 1
        if len(qviews) >= 2:
            rep.cross_view += 1
        t = q.type
        if t is None:
            no_type.append(q.id)
        else:
            types[t] += 1
            if t not in QUESTION_TYPES:
                unknown["type"].append(f"{q.id}:{t}")
        if not q.expected_sql:
            no_sql.append(q.id)
        for kind, names in (("measures", q.measures), ("dimensions", q.dimensions)):
            for name in names:
                credited = False
                view_part, dot, col_part = name.partition(".")
                if dot and view_part.casefold() in by_fold:
                    v = by_fold[view_part.casefold()]
                    c = cols[kind][v].get(col_part.casefold())
                    if c is not None:
                        counters[kind][f"{v}.{c}"] += 1
                        credited = True
                else:
                    for v in qviews or sorted(views):
                        c = cols[kind][v].get(name.casefold())
                        if c is not None:
                            counters[kind][f"{v}.{c}"] += 1
                            credited = True
                if not credited:
                    unknown[kind].append(f"{q.id}:{name}")

    rep.type_mix = dict(sorted(types.items()))
    rep.cross_view_share = rep.cross_view / rep.total if rep.total else 0.0
    problems = rep.problems
    if rep.total < MIN_QUESTIONS:
        problems.append(f"{rep.total} questions; need at least {MIN_QUESTIONS}")
    if rep.total > MAX_QUESTIONS:
        problems.append(f"{rep.total} questions; at most {MAX_QUESTIONS} allowed")
    for v, n in rep.per_view.items():
        if n < MIN_PER_VIEW:
            problems.append(f"metric view {v}: {n} questions; need at least {MIN_PER_VIEW}")
    for kind, counter in (("measures", rep.per_measure), ("dimensions", rep.per_dimension)):
        for v in sorted(views):
            missing = [k.split(".", 1)[1] for k, n in counter.items() if n == 0 and k.split(".", 1)[0] == v]
            if missing:
                problems.append(f"metric view {v}: {kind} never asked about: {_ids(missing)}")
    if rep.cross_view_share < MIN_CROSS_VIEW_SHARE:
        problems.append(
            f"cross-view share {rep.cross_view_share:.1%} ({rep.cross_view}/{rep.total}); "
            f"need at least {MIN_CROSS_VIEW_SHARE:.0%} of questions tagged with two or more views"
        )
    unused = [t for t in QUESTION_TYPES if types[t] == 0]
    if unused:
        problems.append(f"question types not used: {', '.join(unused)}")
    if no_type:
        problems.append(f"{len(no_type)} question(s) without a type: tag: {_ids(no_type)}")
    if no_sql:
        problems.append(f"{len(no_sql)} question(s) without expected_sql: {_ids(no_sql)}")
    for key, label in (
        ("type", "unknown types"),
        ("view", "unknown views"),
        ("measures", "unknown measures"),
        ("dimensions", "unknown dimensions"),
    ):
        if unknown[key]:
            problems.append(f"{label}: {_ids(unknown[key])}")
    return rep


# ---------------------------------------------------------------------------
# Splits and space benchmarks
# ---------------------------------------------------------------------------


def _hash_share(question_id: str) -> float:
    digest = hashlib.sha256(question_id.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") / 2**64


def assign_splits(questions: Iterable[Question], holdout: float = HOLDOUT_SHARE) -> dict[str, str]:
    """Set ``Question.split`` (explicit YAML ``split`` wins) and return ``{id: split}``."""
    if not 0.0 <= holdout < 1.0:
        raise ValueError(f"holdout share must be in [0, 1), got {holdout}")
    out: dict[str, str] = {}
    for q in questions:
        if q.split is None:
            q.split = "holdout" if _hash_share(q.id) < holdout else "tuning"
        out[q.id] = q.split
    return out


def benchmark_id(question_id: str) -> str:
    """Stable 32-character lowercase hex Genie benchmark id for a question id."""
    return uuid.uuid5(_BENCHMARK_NAMESPACE, question_id).hex


def _sql_lines(sql: str) -> list[str]:
    return sql.splitlines(keepends=True) or [""]


def to_space_benchmarks(questions: Iterable[Question]) -> dict[str, Any]:
    """The serialized-space ``benchmarks`` section for ``geniespace.build_space``.

    Raises ``ValueError`` above ``MAX_SPACE_BENCHMARKS`` questions, on a
    duplicate id, or on a question without ``expected_sql``.
    """
    qs = list(questions)
    if len(qs) > MAX_SPACE_BENCHMARKS:
        raise ValueError(f"{len(qs)} benchmark questions; Genie allows at most {MAX_SPACE_BENCHMARKS}")
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for q in qs:
        if q.id in seen:
            raise ValueError(f"duplicate question id '{q.id}'")
        seen.add(q.id)
        if not q.expected_sql:
            raise ValueError(f"'{q.id}': a space benchmark needs expected_sql (its SQL answer)")
        items.append(
            {
                "id": benchmark_id(q.id),
                "question": [q.question],
                "answer": [{"format": "SQL", "content": _sql_lines(q.expected_sql)}],
            }
        )
    return {"questions": sorted(items, key=lambda i: i["id"])}


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
            if len(act) == len(exp) and all(_eq(x, y) for x, y in zip(act, exp, strict=True)):
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


def _fractional(value: Any) -> float | None:
    n = _norm(value)
    if isinstance(n, float) and math.isfinite(n) and not n.is_integer():
        return n
    return None


def _unit_mismatch(rows: list[list[Any]], expected: Any, *, ratio: bool = False) -> bool:
    """True when ``rows`` match ``expected`` with its ratio values x100 or /100."""
    if isinstance(expected, (list, tuple)):
        exp_rows = _as_rows(list(expected))
        if not any(_fractional(c) is not None for r in exp_rows for c in r):
            return False
        for f in UNIT_FACTORS:
            scaled = [[(x * f) if (x := _fractional(c)) is not None else c for c in r] for r in exp_rows]
            if _rows_equal(rows, scaled):
                return True
        return False
    n = _norm(expected)
    if not isinstance(n, float) or n == 0.0 or not rows:
        return False
    if not (ratio or not n.is_integer()):
        return False
    return any(_eq(cell, n * f) for f in UNIT_FACTORS for cell in rows[0])


# ---------------------------------------------------------------------------
# Retries
# ---------------------------------------------------------------------------

_RETRYABLE_NAMES = frozenset(
    {"TooManyRequests", "ResourceExhausted", "InternalError", "TemporarilyUnavailable", "ServiceUnavailable"}
)
_RETRYABLE_CODES = frozenset({"RESOURCE_EXHAUSTED", "TOO_MANY_REQUESTS", "TEMPORARILY_UNAVAILABLE", "INTERNAL_ERROR"})


def _status_code(e: BaseException) -> int | None:
    for holder in (e, getattr(e, "response", None)):
        for attr in ("status_code", "http_status", "status"):
            value = getattr(holder, attr, None)
            if isinstance(value, int) and not isinstance(value, bool):
                return value
    return None


def _is_retryable(e: BaseException) -> bool:
    code = _status_code(e)
    if code is not None:
        return code in RETRY_STATUS
    if type(e).__name__ in _RETRYABLE_NAMES:
        return True
    return str(getattr(e, "error_code", "") or "") in _RETRYABLE_CODES


def _with_backoff(
    fn: Callable[[], T],
    *,
    retries: int = MAX_RETRIES,
    base_s: float = BACKOFF_BASE_S,
    max_s: float = BACKOFF_MAX_S,
) -> T:
    """Call ``fn``; on HTTP 429/5xx wait ``base_s * 2**attempt`` (jittered, capped) and retry."""
    attempt = 0
    while True:
        try:
            return fn()
        except Exception as e:
            if attempt >= retries or not _is_retryable(e):
                raise
            delay = min(max_s, base_s * 2**attempt)
            _sleep(delay * (0.5 + 0.5 * _jitter()))
            attempt += 1


# ---------------------------------------------------------------------------
# Running (fallback: one conversation per question)
# ---------------------------------------------------------------------------


def _get(obj: Any, key: str) -> Any:
    if obj is None:
        return None
    if isinstance(obj, Mapping):
        return obj.get(key)
    return getattr(obj, key, None)


def _state(statement_response: Any) -> str | None:
    state = _get(_get(statement_response, "status"), "state")
    if state is None:
        return None
    return str(getattr(state, "value", state))


def _rows_and_columns(statement_response: Any) -> tuple[list[str], list[list[Any]]]:
    schema = _get(_get(statement_response, "manifest"), "schema")
    columns = [str(_get(c, "name")) for c in (_get(schema, "columns") or [])]
    rows = [list(r) for r in (_get(_get(statement_response, "result"), "data_array") or [])]
    return columns, rows


def _statement_error(statement_response: Any) -> str | None:
    err = _get(_get(statement_response, "status"), "error")
    return _get(err, "message") or (str(err) if err else None)


def _run_expected_sql(ws: Any, warehouse_id: str, sql: str, timeout_s: int) -> list[list[Any]]:
    resp = _with_backoff(
        lambda: ws.statement_execution.execute_statement(
            statement=sql,
            warehouse_id=warehouse_id,
            wait_timeout=f"{min(max(timeout_s, 5), 50)}s",
        )
    )
    if _state(resp) != "SUCCEEDED":
        raise RuntimeError(f"expected_sql did not succeed ({_state(resp)}): {_statement_error(resp)}")
    return _rows_and_columns(resp)[1]


def _ask(space_id: str, q: Question, ws: Any, timeout_s: int, warehouse_id: str | None) -> Result:
    r = Result(question_id=q.id, question=q.question, tags=list(q.tags), split=q.split)
    start = time.monotonic()
    try:
        msg = _with_backoff(
            lambda: ws.genie.start_conversation_and_wait(space_id, q.question, timeout=timedelta(seconds=timeout_s))
        )
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
            attachment_id = att.attachment_id

            def _query_result(aid: str = attachment_id) -> Any:
                return ws.genie.get_message_attachment_query_result(space_id, r.conversation_id, r.message_id, aid)

            qr = _with_backoff(_query_result)
            stmt = getattr(qr, "statement_response", None)
            if _state(stmt) == "SUCCEEDED":
                r.sql_succeeded = True
                r.columns, r.rows = _rows_and_columns(stmt)
            else:
                r.error = r.error or f"query state {_state(stmt)}: {_statement_error(stmt)}"
        r.text = "\n\n".join(texts) or None

        if q.expected_answer is not None:
            r.matches_expected = r.sql_succeeded and _match_answer(r.rows, q.expected_answer)
            if r.sql_succeeded and not r.matches_expected:
                r.unit_mismatch = _unit_mismatch(r.rows, q.expected_answer, ratio=q.type == "ratio")
        elif q.expected_sql and warehouse_id:
            r.matches_expected = False
            if r.sql_succeeded:
                expected_rows = _run_expected_sql(ws, warehouse_id, q.expected_sql, timeout_s)
                r.matches_expected = _rows_equal(r.rows, expected_rows)
                if not r.matches_expected:
                    r.unit_mismatch = _unit_mismatch(r.rows, expected_rows)
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
    max_workers: int = 4,
) -> list[Result]:
    """Ask each question in a new conversation and capture SQL + result.

    ``ws`` is a ``databricks.sdk.WorkspaceClient`` (uses ``ws.genie`` and, for
    ``expected_sql`` with ``warehouse_id``, ``ws.statement_execution``). At most
    ``max_workers`` questions run at once (Genie API requests are rate-limited
    per workspace); HTTP 429/5xx are retried with exponential backoff and
    ``timeout_s`` bounds each question. Errors and timeouts are recorded on the
    ``Result`` (``error``) and the run continues. Results keep the question
    order. Only the first chunk of each query result is read.
    """
    qs = list(questions)
    if max_workers <= 1 or len(qs) <= 1:
        return [_ask(space_id, q, ws, timeout_s, warehouse_id) for q in qs]
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        return list(pool.map(lambda q: _ask(space_id, q, ws, timeout_s, warehouse_id), qs))


# ---------------------------------------------------------------------------
# Genie benchmark evaluation runs
# ---------------------------------------------------------------------------


@dataclass
class EvalRun:
    """One Genie benchmark evaluation run and its per-question results."""

    space_id: str
    eval_run_id: str
    status: str | None = None
    num_questions: int | None = None
    num_done: int | None = None
    num_correct: int | None = None
    num_needs_review: int | None = None
    started_at: str | None = None
    results: list[Result] = field(default_factory=list)
    needs_review: list[str] = field(default_factory=list)


def _api(ws: Any, method: str, path: str, *, body: Any = None, query: Any = None) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    if body is not None:
        kwargs["body"] = body
    if query is not None:
        kwargs["query"] = query
    resp = _with_backoff(lambda: ws.api_client.do(method, path, **kwargs))
    return resp if isinstance(resp, dict) else {}


def _enum_value(value: Any) -> str | None:
    if value is None:
        return None
    return str(getattr(value, "value", value))


def _question_text(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return "".join(str(v) for v in value).strip()
    return str(value or "").strip()


def _eval_result(item: Mapping[str, Any], details: Mapping[str, Any], q: Question | None) -> Result:
    bid = str(item.get("benchmark_question_id") or details.get("benchmark_question_id") or "")
    r = Result(
        question_id=q.id if q else bid,
        question=q.question if q else _question_text(item.get("question")),
        tags=list(q.tags) if q else [],
        split=q.split if q else None,
        status=_enum_value(details.get("eval_run_status") or item.get("status")),
    )
    # ``assessment`` is the verdict. ``manual_assessment`` only says whether a
    # reviewer set it (API: "Whether this evaluation was manually assessed").
    assessment: str | None = _enum_value(details.get("assessment"))
    r.assessment = assessment
    r.matches_expected = assessment == "GOOD"
    r.needs_review = assessment not in ("GOOD", "BAD")

    texts: list[str] = []
    for resp in details.get("actual_response") or []:
        rtype = _enum_value(_get(resp, "response_type"))
        content = _get(resp, "response")
        if rtype == "SQL" and not r.sql_generated and content and str(content).strip():
            r.sql, r.sql_generated = str(content).strip(), True
            stmt = _get(resp, "sql_execution_result")
            if _state(stmt) == "SUCCEEDED":
                r.sql_succeeded = True
                r.columns, r.rows = _rows_and_columns(stmt)
            elif stmt is not None:
                r.error = f"query state {_state(stmt)}: {_statement_error(stmt)}"
        elif rtype == "TEXT" and content:
            texts.append(str(content))
    r.text = "\n\n".join(texts) or None

    if r.sql_succeeded and not r.matches_expected:
        for resp in details.get("expected_response") or []:
            stmt = _get(resp, "sql_execution_result")
            if _state(stmt) == "SUCCEEDED":
                r.unit_mismatch = _unit_mismatch(r.rows, _rows_and_columns(stmt)[1])
                break
    return r


def run_eval(
    space_id: str,
    ws: Any,
    question_ids: Iterable[str] | None = None,
    poll_s: float = 10,
    timeout_s: float = 7200,
    *,
    questions: Iterable[Question] | None = None,
) -> EvalRun:
    """Run a Genie benchmark evaluation and return its results as ``Result`` objects.

    ``question_ids`` limits the run to those questions (their ``benchmark_id``
    must be in the agent's benchmarks, see ``to_space_benchmarks``); ``None``
    runs every benchmark. ``questions`` maps Genie benchmark ids back to
    question ids, tags and splits (unmapped results keep the Genie id). Raises
    ``TimeoutError`` after ``timeout_s`` and ``RuntimeError`` when the run ends
    in a status other than ``DONE``. See the module docstring for the mapping.
    """
    by_bid: dict[str, Question] = {}
    by_text: dict[str, Question] = {}
    for q in questions or []:
        by_bid[benchmark_id(q.id)] = q
        by_text.setdefault(q.question.casefold(), q)
    base = f"/api/2.0/genie/spaces/{space_id}/eval-runs"
    body: dict[str, Any] = {}
    if question_ids is not None:
        body["benchmark_question_ids"] = [benchmark_id(qid) for qid in question_ids]
    started_at = datetime.now(UTC).isoformat(timespec="seconds")
    run = _api(ws, "POST", base, body=body)
    run_id = str(run.get("eval_run_id") or "")
    if not run_id:
        raise RuntimeError(f"eval run was not created for space {space_id}: {run}")

    deadline = time.monotonic() + timeout_s
    delay = max(float(poll_s), 0.0)
    while _enum_value(run.get("eval_run_status")) in (None, *EVAL_RUNNING):
        if time.monotonic() > deadline:
            raise TimeoutError(f"eval run {run_id} still {_enum_value(run.get('eval_run_status'))} after {timeout_s}s")
        _sleep(delay)
        delay = min(max(delay * 1.5, 1.0), POLL_MAX_S)
        run = _api(ws, "GET", f"{base}/{run_id}")
    status = _enum_value(run.get("eval_run_status"))
    if status != "DONE":
        raise RuntimeError(f"eval run {run_id} ended {status}")

    out = EvalRun(
        space_id=space_id,
        eval_run_id=run_id,
        status=status,
        num_questions=run.get("num_questions"),
        num_done=run.get("num_done"),
        num_correct=run.get("num_correct"),
        num_needs_review=run.get("num_needs_review"),
        started_at=started_at,
    )
    token: str | None = None
    while True:
        query: dict[str, Any] = {"page_size": EVAL_PAGE_SIZE}
        if token:
            query["page_token"] = token
        page = _api(ws, "GET", f"{base}/{run_id}/results", query=query)
        for item in page.get("eval_results") or []:
            details = _api(ws, "GET", f"{base}/{run_id}/results/{item.get('result_id')}")
            bid = str(item.get("benchmark_question_id") or details.get("benchmark_question_id") or "")
            match = by_bid.get(bid) or by_text.get(_question_text(item.get("question")).casefold())
            r = _eval_result(item, details, match)
            out.results.append(r)
            if r.needs_review:
                out.needs_review.append(r.question_id)
        token = page.get("next_page_token") or None
        if not token:
            break
    return out


# ---------------------------------------------------------------------------
# Scoring and reporting
# ---------------------------------------------------------------------------


def score(results: Iterable[Result], splits: Mapping[str, str] | None = None) -> Summary:
    """Summarize results; see the module docstring for the definition.

    ``splits`` (``{question_id: split}``, e.g. from ``assign_splits``)
    overrides ``Result.split`` for the per-split accuracy.
    """
    results = list(results)
    s = Summary(total=len(results))
    s.sql_generated = sum(r.sql_generated for r in results)
    s.sql_succeeded = sum(r.sql_succeeded for r in results)
    s.with_expectations = sum(r.matches_expected is not None for r in results)
    s.matches_expected = sum(r.matches_expected is True for r in results)
    s.errors = sum(r.error is not None for r in results)
    s.unit_mismatch = sum(r.unit_mismatch for r in results)
    s.needs_review = sum(r.needs_review for r in results)
    if s.with_expectations:
        s.accuracy, s.accuracy_basis = s.matches_expected / s.with_expectations, "expected"
    elif s.total:
        s.accuracy, s.accuracy_basis = s.sql_succeeded / s.total, "succeeded"
    for name in SPLITS:
        scored = [
            r for r in results if r.matches_expected is not None and (splits or {}).get(r.question_id, r.split) == name
        ]
        setattr(s, name, _split_block(len(scored), sum(r.matches_expected is True for r in scored)))
    return s


def _cell(value: Any, limit: int = 120) -> str:
    text = "" if value is None else " ".join(str(value).split())
    if len(text) > limit:
        text = text[: limit - 3] + "..."
    return text.replace("|", "\\|")


def _yn(value: bool | None) -> str:
    return "n/a" if value is None else ("yes" if value else "no")


def _split_cell(block: Mapping[str, Any]) -> str:
    return f"{block['accuracy']:.1%} ({block['correct']}/{block['n']})"


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
        f"| Unit mismatches | {summary.unit_mismatch} |",
        f"| Needs review | {summary.needs_review} |",
        f"| Accuracy | {summary.accuracy:.1%} ({summary.accuracy_basis}) |",
        f"| Tuning accuracy | {_split_cell(summary.tuning)} |",
        f"| Holdout accuracy | {_split_cell(summary.holdout)} |",
        f"| Gate (>= {ACCURACY_GATE:.0%}) | {gate} |",
        "",
        "## Questions",
        "",
        "| ID | Question | Split | SQL generated | SQL succeeded | Matches expected | Unit mismatch "
        "| Interpretation | Tags | Error |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {_cell(r.question_id)} | {_cell(r.question)} | {_cell(r.split)} | {_yn(r.sql_generated)} "
            f"| {_yn(r.sql_succeeded)} | {_yn(r.matches_expected)} | {_yn(r.unit_mismatch)} |  "
            f"| {_cell(', '.join(r.tags))} | {_cell(r.error)} |"
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


# ---------------------------------------------------------------------------
# Accuracy history and the stop rule
# ---------------------------------------------------------------------------


def history_entry(
    iteration: int,
    label: str,
    summary: Summary,
    *,
    eval_run_id: str | None = None,
    started_at: str | None = None,
    changes: Sequence[Any] | None = None,
) -> dict[str, Any]:
    """An ``accuracy_history.json`` entry from a scored run."""
    return {
        "iteration": int(iteration),
        "label": label,
        "eval_run_id": eval_run_id,
        "started_at": started_at or datetime.now(UTC).isoformat(timespec="seconds"),
        "tuning": dict(summary.tuning),
        "holdout": dict(summary.holdout),
        "changes": list(changes or []),
    }


def append_history(path: str | Path, entry: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Append ``entry`` to the JSON history list at ``path`` (created if missing); return the history.

    Raises ``ValueError`` when ``entry`` lacks ``iteration``/``tuning``/``holdout``
    or its iteration is already recorded.
    """
    missing = [k for k in ("iteration", "tuning", "holdout") if k not in entry]
    if missing:
        raise ValueError(f"history entry is missing {missing}")
    p = Path(path)
    history = json.loads(p.read_text(encoding="utf-8")) if p.exists() else []
    if not isinstance(history, list):
        raise ValueError(f"{p}: expected a JSON list")
    if any(int(h.get("iteration", -1)) == int(entry["iteration"]) for h in history):
        raise ValueError(f"{p}: iteration {entry['iteration']} is already recorded")
    history.append(dict(entry))
    history.sort(key=lambda h: int(h.get("iteration", 0)))
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(history, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return history


def _pct(block: Any) -> float | None:
    if not isinstance(block, Mapping):
        return None
    acc = block.get("accuracy")
    if acc is None and block.get("n"):
        acc = block.get("correct", 0) / block["n"]
    return None if acc is None else round(float(acc) * 100.0, 4)


def asymptote(history: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Apply the stop rule (module docstring) to an accuracy history.

    Returns ``{reached, reason, fix_iterations, last_deltas_pp,
    holdout_gap_pp, exhausted}``.
    """
    entries = sorted(history, key=lambda h: int(h.get("iteration", 0)))
    fix_iterations = sum(int(h.get("iteration", 0)) >= 1 for h in entries)
    tuning = [_pct(h.get("tuning")) for h in entries]
    deltas: list[float] = []
    if len(tuning) > ASYMPTOTE_WINDOW and all(t is not None for t in tuning[-ASYMPTOTE_WINDOW - 1 :]):
        window = [float(t) for t in tuning[-ASYMPTOTE_WINDOW - 1 :] if t is not None]
        deltas = [round(b - a, 4) for a, b in zip(window[:-1], window[1:], strict=True)]
    holdout = [p for p in (_pct(h.get("holdout")) for h in entries) if p is not None]
    gap = round(max(holdout) - holdout[-1], 4) if holdout else None
    out: dict[str, Any] = {
        "reached": False,
        "reason": "",
        "fix_iterations": fix_iterations,
        "last_deltas_pp": deltas,
        "holdout_gap_pp": gap,
        "exhausted": False,
    }
    latest = tuning[-1] if tuning else None
    if fix_iterations < MIN_FIX_ITERATIONS:
        out["reason"] = f"{fix_iterations} tuning plan(s) applied; the stop rule needs at least {MIN_FIX_ITERATIONS}"
    elif latest is None or gap is None:
        out["reason"] = "the latest iteration has no tuning or holdout accuracy"
    else:
        at_max = latest >= 100.0 - 1e-9
        flat = len(deltas) == ASYMPTOTE_WINDOW and all(d < ASYMPTOTE_DELTA_PP for d in deltas)
        if not (at_max or flat):
            out["reason"] = (
                f"tuning accuracy still improving: last {ASYMPTOTE_WINDOW} deltas {deltas} pp "
                f"(each must be < {ASYMPTOTE_DELTA_PP})"
            )
        elif gap > HOLDOUT_TOLERANCE_PP + 1e-9:
            out["reason"] = f"holdout accuracy is {gap} pp below its best (tolerance {HOLDOUT_TOLERANCE_PP})"
        else:
            out["reached"] = True
            plateau = (
                "tuning accuracy reached 100%"
                if at_max
                else f"tuning accuracy gained < {ASYMPTOTE_DELTA_PP} pp in each of the last "
                f"{ASYMPTOTE_WINDOW} iterations"
            )
            out["reason"] = f"{plateau}; holdout within {HOLDOUT_TOLERANCE_PP} pp of its best"
    if not out["reached"] and fix_iterations >= MAX_FIX_ITERATIONS:
        out["exhausted"] = True
        out["reason"] += f"; {fix_iterations} tuning plans applied without reaching the asymptote"
    return out


def write_iteration_md(
    path: str | Path,
    entry: Mapping[str, Any],
    *,
    state: Mapping[str, Any] | None = None,
    results: Iterable[Result] | None = None,
    plan_applied: str | None = None,
    next_plan: str | None = None,
) -> Path:
    """Write ``iterations/<k>.md``: accuracy, changes, stop-rule state and tuning failures.

    Only ``tuning``-split failures are listed; holdout failures are counted,
    never shown (tuning sessions must not read them).
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tuning, holdout = entry.get("tuning") or {}, entry.get("holdout") or {}

    def block(b: Mapping[str, Any]) -> str:
        pct = _pct(b)
        return "n/a" if pct is None else f"{pct:.1f}% ({b.get('correct', 0)}/{b.get('n', 0)})"

    lines = [
        f"# Tuning iteration {entry.get('iteration')}: {entry.get('label') or ''}".rstrip(),
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Eval run | {_cell(entry.get('eval_run_id'))} |",
        f"| Started | {_cell(entry.get('started_at'))} |",
        f"| Tuning accuracy | {block(tuning)} |",
        f"| Holdout accuracy | {block(holdout)} |",
    ]
    if plan_applied:
        lines.append(f"| Plan applied | {_cell(plan_applied)} |")
    if next_plan:
        lines.append(f"| Next plan | {_cell(next_plan)} |")
    if state is not None:
        lines += [
            f"| Asymptote reached | {_yn(bool(state.get('reached')))} |",
            f"| Stop rule | {_cell(state.get('reason'), limit=400)} |",
            f"| Last deltas (pp) | {_cell(state.get('last_deltas_pp'))} |",
            f"| Holdout gap (pp) | {_cell(state.get('holdout_gap_pp'))} |",
        ]
    lines += ["", "## Changes", ""]
    changes = list(entry.get("changes") or [])
    lines += [f"* {_cell(c, limit=400)}" for c in changes] or ["_None._"]
    if results is not None:
        failures = [r for r in results if r.split == "tuning" and r.matches_expected is False]
        lines += [
            "",
            "## Tuning failures",
            "",
            "Holdout failures are not listed.",
            "",
            "| ID | Question | SQL succeeded | Unit mismatch | Needs review | Error |",
            "|---|---|---|---|---|---|",
        ]
        lines += [
            f"| {_cell(r.question_id)} | {_cell(r.question)} | {_yn(r.sql_succeeded)} | {_yn(r.unit_mismatch)} "
            f"| {_yn(r.needs_review)} | {_cell(r.error)} |"
            for r in failures
        ]
    p.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m genie_ontology_modeled_knowledge_sdk.benchmark")
    sub = parser.add_subparsers(dest="command", required=True)
    cov = sub.add_parser("coverage", help="check a question set's coverage of the metric views")
    cov.add_argument("questions_dir")
    cov.add_argument("metric_views_dir")
    cov.add_argument("--json", action="store_true", help="print the report as JSON")
    args = parser.parse_args(argv)
    try:
        report = coverage(load_question_set(args.questions_dir), args.metric_views_dir)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True) if args.json else report.to_text())
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
