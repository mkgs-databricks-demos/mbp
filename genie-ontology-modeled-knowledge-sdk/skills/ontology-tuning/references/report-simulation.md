# Independent Report Simulation (final evaluation)

The final evaluation of a tuned Genie Agent. It tests what one-question benchmarks cannot: follow-ups that rely on earlier turns, drill-downs, period comparisons and assembling a narrative a business user could send. It runs in a **separate session** from tuning. Persona, turn and target values below come from the protocol table in the build plan index ("Exhaustive tuning protocol"); they are protocol settings, not `benchmark` constants, so take them from the run kit plan when it differs.

## Independence rules

* Do **not** read `docs/tuning/**` (benchmarks, iterations, tuning plans, summary), and do not read the agent file's instructions, example SQL or benchmarks.
* Allowed inputs: `docs/research/`, `docs/semantics/`, `docs/data_profiles/`, `docs/domain_manifest.yml`, `docs/deployment/` (for the space id).
* Ground truth is computed on the **source tables**, never on the metric views, so a metric view defect cannot hide itself.
* List every file you read in the session summary.

## Method

1. **Personas.** 4-5 report personas in `docs/evaluation/personas.md`, each with a report brief (audience, decisions the report supports, period, grain). Cover different subdomains and at least one cross-view report (for example revenue vs cost).
2. **Turns, written before asking Genie.** 8-15 turns per report, in order, including at least 3 follow-ups that depend on earlier turns ("now only for Europe", "and the same for the prior year", "which of those suppliers ..."). Do not reword turns after the run starts.
3. **Pre-registered ground truth.** For each turn, read-only SQL over the source tables in `docs/evaluation/ground_truth/<report>.sql` (one statement per turn, numbered comments). Run each statement; it must reach `SUCCEEDED`. Record the results and the run timestamp before the first Genie turn.
4. **One conversation per report.** `ws.genie.start_conversation_and_wait(space_id, turn_1)`, then each later turn as a follow-up message in the same conversation. Capture per turn: SQL, result rows, text, status.
5. **Grade each turn** against its ground truth:

   | Grade | Meaning |
   |---|---|
   | `correct` | numbers equal within the `benchmark` comparison tolerance (`REL_TOL`, relative 1e-4), right grain and filters |
   | `partial` | right numbers, wrong presentation or a missing part |
   | `wrong` | wrong numbers, grain or filter |
   | `no_answer` | no SQL, an error, or a refusal |

   Per report also record **completeness** (all brief items covered) and **sendable as-is** (yes/no with a reason).
6. **Score.** Per report: (`correct` + 0.5 x `partial`) / turns. Overall: the same over all turns. Target: 80% overall. The target is recorded, not gated; a lower score becomes a backlog item.

## Outputs

| File | Contents |
|---|---|
| `docs/evaluation/personas.md` | personas, briefs, turns |
| `docs/evaluation/ground_truth/<report>.sql` | pre-registered SQL per turn, with result snapshot and timestamp |
| `docs/evaluation/reports/<report>.md` | the report as Genie produced it, turn by turn |
| `docs/evaluation/report_simulation_results.md` | rubric, per-turn grades, per-report and overall score, failure themes |

## Failure themes

Map each wrong or partial turn to the likely fix layer, using the tuning fix ladder: metric view (steps 1-7), glossary / UC Page (step 8) or agent (steps 9-10). Themes feed the next tuning cycle as backlog items; the simulation itself changes nothing.
