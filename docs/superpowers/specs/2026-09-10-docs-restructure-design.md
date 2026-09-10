---
title: "Docs restructure — design and gap register"
date: 2026-09-10
status: implemented (restructure and figures), open (2 register items)
---

# Docs restructure — design and gap register

## The problem

`lex-app-docs` had 66 published pages and ~48,000 words. Depth was not the
problem — `features/` averaged 973 words a page, `reference/` 824, `tutorial/`
940. Three things were:

1. **The top level mixed three organising ideas.** Subject (`features`,
   `interface`), content type (`reference`, `tutorial`) and situation
   (`migration`). Nothing about it told a reader where they were or what came
   next.
2. **The entry funnel was thin and doubled.** `index.md` (229 words) and
   `getting started.md` (179) both tried to be the front door. `getting
   started` then routed "business analysts" to
   `features/processing/calculations` and `features/access-and-ui/permissions`
   — developer API pages. That routing was wrong, not merely unhelpful.
3. **Gaps against the shipped product**, listed in the register below.

## Decisions

| Decision | Chosen | Why |
|---|---|---|
| Audience | Both, in one tree | Considered splitting build-vs-use at the top; judged not the main problem. |
| Top level | By task, in the order you hit it | The old level mixed taxonomies; a journey ordering answers "where am I, what's next". |
| Rewrite scope | Entries and landings only | Depth was fine. Effort goes where the deficiency is. |
| Register order | Blocking-first, then newest | Fix "not understandable" before "not complete". |
| Execution | Move + mechanical link rewrite + aliases, staged | 252 of 269 wikilinks carry explicit paths, so 93% break on a move. |
| Screenshots | Deferred to commented `📸 TODO` placeholders | Per instruction; the capture pipeline exists separately. |

## The tree

```
index.md                    home — one front door (aliases: home, getting started, features/index)
start-here/                 installation · project structure · running your app · tutorial/
model-your-data/            ← features/data-pipeline
calculations/               ← features/processing  (+ scheduled calculations)
history-and-audit/          ← features/tracking
access-and-dashboards/      ← features/access-and-ui  (+ widgets)
ship-and-operate/           NEW
using-the-app/              ← interface
reference/                  unchanged
migrating-from-v1/          ← migration
```

Order is enforced by `explorerOptions.sortFn` in `quartz.layout.ts`.
Alphabetical sorting would put "Start Here" ninth and the tutorial above the
installation page it depends on. The ranking lives **inside** the function
because Explorer serialises it with `.toString()` and re-evaluates it in the
browser.

## Constraints discovered

- **`lex-app/docs/` is a read-only mirror** of `lex-app-docs/content`, driven
  by `docs/.docs-sync.yml`. A renamed section must be renamed in
  `managed_paths` or the sync mirrors nothing while stale local copies
  persist. Updated in `docs/restructure-mirror`.
- **`lex --help` lists 10 of ~26 commands.** `main()` skips Django bootstrap
  for help, so every management passthrough and the `ai-*` family are
  invisible. The docs are the only complete command reference; the home page
  now says so.
- **Branch ruleset allows creating a branch but not updating one.** Each stage
  pushes to a new branch (`…-s2`, `-s3`, …).

## Gap register

Blocking-first, then newest. Status as of 2026-09-10.

| # | Page | Evidence | Status |
|---|---|---|---|
| 1 | `ship-and-operate/` (6 pages) | 0 pages on backup, 1 on Kubernetes, 1 on troubleshooting; "running your app" 325 words | **done** |
| 2 | `ship-and-operate/upgrading` | No page existed; 2.1.11's `max_length` migration had no home | **done** |
| 3 | `access-and-dashboards/widgets` | `WidgetPage`, `WidgetSpecError`, `lex_calculation_log`, `lex_calculation_log_tree` exported and undocumented — the 2.2.0 flagship | **done** |
| 4 | `calculations/scheduled calculations` | Written in lex-app under a mirror-managed path; guard-rejected, never published | **done** |
| 5 | `access-and-dashboards/embedding` | Planned | **declined** — `lex_view callbacks` and `streamlit dashboards` already cover both directions |
| 6 | Screenshots | 9 placeholders | **7 done** — record page + 4 tabs, the grid, table settings, `lex --help`; `deploying` got a mermaid diagram instead |
| 7 | Analytics tab + widgets figures | Both prerequisites are now done — the fixture has `Fund.streamlit_main` and the harness starts `lex streamlit` behind `LEX_DOCSHOT_STREAMLIT=1`. Still blocked one level down: the Streamlit proxy wants a Keycloak JWT, the harness signs in with a Django admin session | blocked on fixture auth; capture exists and is skipped |
| 8 | `reference/` completeness sweep | Not yet audited name-by-name against `__all__` and the env-var list | open |
| 9 | Backup and restore | Named as absent; no framework-side facts verified yet, so not written | open |

Items 8 and 9 are deliberately not started. 8 needs a mechanical audit that
should be a CI check rather than prose. 9 needs facts from whoever operates
the databases — writing it from assumption is how operational documentation
becomes dangerous.

## Verification

`scripts/check_links.py` in `lex-app-docs` gates every stage. Baseline before
the move and after every commit: 0 broken, 0 ambiguous, 0 missing. It found
four of its own bugs and two real ones (a dangling link to the declined
`embedding` page, and the `features/index` links left by the fold).

## Branches

| Branch | Repo | Contains |
|---|---|---|
| `docs/restructure-2026-09-s8` | lex-app-docs | The restructure and the figures (all stages) |
| `docs/restructure-mirror-s4` | lex-app | The mirror manifest, stale-copy removal, this spec |
| `feat/docs-figures-s3` | lex-app | The renderer and figures spec |
| `docs/figure-captures` | process-admin-general-client | The capture harness and the dashboard fixture |

## What the figure pipeline learned

Worth carrying into anything similar. Every one of these produced a wrong
figure before it produced a rule:

- A resolved anchor is not a usable screen. The Analytics capture made a
  clean, correct photograph of an authentication error.
- Measure and photograph in one settled layout, then check it did not move.
  A uniformly-offset figure is undetectable by eye once built.
- Clamp a box that overflows the picture; REJECT one entirely outside it.
  Conflating those marks controls that were never photographed.
- Place a mark by the target's size. Lanes suit a column of switches and are
  wrong for a row of tabs, where they drag leaders across the whole image.
