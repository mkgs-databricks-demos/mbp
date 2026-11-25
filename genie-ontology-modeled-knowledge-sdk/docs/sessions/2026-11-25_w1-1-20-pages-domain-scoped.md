# 2026-11-25 - Wave 1-1, session 20: Pages domain-scoped upserts, drafts, bulk terms (R4.2)

Run `1057400752545739`, branch `mg-genie-ontology-build-1-plan`, mode `edit`. No Git commands that change state were run (read-only `git status` only). No live API calls; mocked tests only.

## Problems and root causes

* G6 / obs 21: `upsert_pages` without `domain_id` listed every page in the account and updated any page with a matching title, so it could overwrite another team's page.
* Obs 22: the 160-character description could cut a markdown link in half.
* Obs 8: writing one file per term cost two tool calls per term.

## Changes (`src/genie_ontology_modeled_knowledge_sdk/pages.py`)

* `upsert_pages(terms, client, *, domain_id=None, dry_run=True, status="DRAFT", only_ids=None)`:
  * A live run without `domain_id` returns an `error` result for every term (`reason` starts with `no_domain_id`) and makes no client calls at all.
  * Titles are matched only among `client.list_pages(domains/<id>)`. A page whose `domain` field names another domain is never fetched for update or written, even if a client ignores the filter (defensive check on both the listing and `get_page`).
  * Dry runs also call `list_pages(None)` to report same-title pages in other domains: `reason="collision_other_domain"`, ids in `collisions`. If that listing is refused, the domain result is still returned with `collision check unavailable: ...` in `reason`. Live runs list only the domain.
  * `only_ids`: when given, only those page ids are updated; any other same-title page in the domain is `skipped` with `reason="exists_not_owned"`.
  * `status`: `DRAFT` (the default, sent by omitting `state`) or `PUBLISHED` (sent as `state`); anything else raises `ValueError`. An existing page's state is never changed.
  * Dry run without `domain_id`: every term is `skipped` (`no_domain_id`), with collisions listed.
* `PageResult`: actions are now `created`, `updated`, `unchanged`, `skipped`, `error`. There are new fields `status`, `reason` and `collisions`. `error` is now a read-only property (`reason` when the action is `error`), so build-0 callers that read `r.error` keep working.
* `created_ids(results)`: ids of the pages a live run created.
* `format_registration_table(results)`: a `Domain: development domain` line, then a `Term | Page id | Status | Action` table (dry-run actions are marked `(dry run)`). No domain id is written.
* Descriptions: `_strip_links` turns markdown links (inline, image, reference, autolink) into their text before the sentence split and truncation. `_truncate` drops a bare URL that crosses the cut instead of splitting it.
* `render_term_file(term)` and `write_terms(terms, folder)`: write many term files in one call from `Term` objects or mappings. Each term goes to `<slug>.md`, or to the existing file that already holds the term. A file is not rewritten when its content is unchanged. Duplicate terms, unknown keys, and sections that would not parse back (a nested `## ` heading, or an extra section named like a built-in one) raise `ValueError` before anything is written.
* Module docstring and `__all__` updated (also exports `PAGE_STATUSES`).

## Tests (`tests/test_pages.py`)

Updated the existing tests for the new action names. New tests:

* `test_live_upsert_without_domain_writes_nothing`: no writes, no calls, pages unchanged.
* `test_same_title_page_in_other_domain_is_never_updated`: the dry run reports the collision. The live run creates a new page in the domain, leaves the other page byte-identical, and lists only `domains/<DOMAIN>`.
* `test_other_domain_page_is_never_updated_even_if_client_ignores_filter`.
* `test_not_owned_same_title_page_in_domain_is_skipped`: the page is skipped, then updated once its id is in `only_ids`, and its state stays `PUBLISHED`.
* `test_status_option_for_new_pages`, `test_dry_run_without_domain_reports_collisions_only`, `test_dry_run_collision_check_refused_keeps_domain_result`, `test_format_registration_table_hides_domain`.
* `test_description_strips_link_starting_at_character_150` (asserts the `[` is at index 150), `test_description_link_forms` (4 link forms), `test_bare_url_at_the_cut_is_dropped_whole`.
* `test_write_terms_round_trips_through_parse_glossary`: the fixture glossary written and parsed back gives equal `Term`s, and a second call does not change file mtimes. Also `test_write_terms_accepts_mappings_and_updates_in_place` and `test_write_terms_rejects_bad_input_before_writing`.

No fixture changes were needed (`tests/fixtures/glossary/**` untouched).

## Checks (fresh `/tmp/gos-s20` copy, `GENIE_BUILD_WAVES_DIR` set)

| Check | Result |
|---|---|
| pytest `tests/test_pages.py` | pass: 40 passed |
| pytest (all) | pass: 325 passed |
| ruff check . | pass |
| ruff format --check . | pass (30 files) |
| mypy src | pass (9 source files) |
| bundle validate | skipped: no YAML touched |

An earlier full run, made while session 21 was still editing its files, showed 3 failures in `test_scaffold.py` and the template bundle tests. Those files belong to session 21. The final run passed with all 325 tests.

## Decisions

* Kept `PageResult.error` as a property so existing callers that read it still work. The action names changed as the plan required (`create` -> `created`, `update` -> `updated`).
* In dry runs, the in-domain set comes from the domain-scoped listing, not from the `domain` field of the account-wide listing. Page summaries may omit `domain`, and this keeps the dry-run and live results the same.

## Requests for other sessions

* Session 31 (and the tuning sessions 36-41 that share it): `examples/tpch/docs/pages/pages_registration.md` counts the actions `create`/`update`. Switch to `created`/`updated`/`skipped`, pass `domain_id` and `only_ids` for live runs, and use `format_registration_table` / `created_ids` for the registration record.
* Session 28: `templates/run/plans/07_uc_pages.md` documents `upsert_pages(terms, client, dry_run=True)`. Document the new `domain_id` / `status` / `only_ids` parameters and `write_terms`.
* Session 25 (skills): the skill text that calls `upsert_pages` or writes term files one by one should use `write_terms` and the new actions.
* Owner: `docs/plans/INDEX.md` line 116 still shows the build-0 `upsert_pages` signature (a plan file, read-only to sessions).
