# Streamlit widget API — one flat `lex_*` family, and keys stop being the author's problem

**Date:** 2026-09-07
**Issues:** LEX-708 (naming), LEX-709 (unique keys)
**Status:** proposed — one open decision, marked below

---

## Decisions already taken

**`lex_view` keeps its name.** Customers write against it today, so renaming means a
deprecation cycle to buy a word.

**`lex_view` also becomes the pattern.** Every single-widget surface gets a flat
`lex_*` function beside it, called the same way. The prefix is the family; the rest of
the name says what it embeds.

```python
lex_view("quarter")                             # a whole lex-app route
lex_calculation("navcalc", pk=1)                # one calculation control
lex_calculation_log("navcalc", pk=1)            # the live log
lex_calculation_log_tree("navcalc", pk=1)       # the consolidated run
```

This is what settles LEX-708 without renaming anything customers depend on. The rule
that decides where a future surface belongs becomes stateable in one line: *a flat
`lex_*` function embeds exactly one thing; `lex_widgets()` embeds several into one
frame.* Nothing has to be memorised, because the shape of the call says which you are
looking at.

**`lex_widgets()` stays, for batching only.** It is the form that puts N widgets in one
iframe instead of N React runtimes, and that is the only reason to reach for it.

---

## Problem 1 — the block is mandatory even for one widget

Rendering a single Calculate button costs a context manager:

```python
with lex_widgets() as page:
    page.calculation("navcalc", pk=1, variant="action")
```

`WidgetPage` collects specs and the host only renders in `__exit__`, so there is no
path to one widget without opening a block. For the batch case the block earns its
keep. For one widget it is ceremony, and it is ceremony in a place where the reader
already knows the flat `lex_view(...)` shape.

### The change

Each widget method gains a flat function. The block form is untouched.

```python
# one widget — flat, like lex_view
lex_calculation("navcalc", pk=1, variant="action")

# several — one host, as today
with lex_widgets() as page:
    page.calculation("navcalc", pk=1)
    page.calculation_log_tree("navcalc", pk=1)
```

### How, and why it cannot drift

Each flat function **is** the block form, entered and exited in one call:

```python
def lex_calculation(*args, **kwargs):
    with lex_widgets() as page:
        return page.calculation(*args, **kwargs)
```

No second rendering path, no second manifest builder, no second place for a bug to
live. That property matters more than the brevity: a parallel single-widget
implementation is how two entry points start disagreeing about what a widget is.

Return-value semantics are preserved exactly. `page.calculation(...)` returns the
envelope stored by the *previous* script run, read from `session_state` during
`__enter__`; the flat form runs `__enter__` → method → `__exit__` in that order, so it
reads the same slot at the same moment.

### Discoverability, which is currently zero

`lex/lex_app/streamlit/__init__.py` is **empty**. Every import today reaches through a
deep path (`lex.lex_app.streamlit.widgets.host`), so nothing is discoverable by
autocomplete and no single place shows what the family contains. The flat functions,
`lex_view`, and `lex_widgets` all get exported there, which is what makes "same as
`lex_view`" true at the import line as well as the call site.

### The cost, stated plainly

Each flat call is its own iframe, so its own React runtime. That is the right trade for
one or two controls and the wrong one for ten. The docstrings will say so, and a page
that exceeds a threshold of flat hosts emits a Streamlit warning naming the block
form — a nudge where it starts to matter, not a rule.

---

## Problem 2 — keys are the author's discipline (LEX-709)

### What was verified first, because the issue asked for it

LEX-709 states the change is non-trivial because "DOM ids collide so CSS written for
one widget lands on another", and asks for that to be checked before implementing
rather than after. It was checked. **It does not hold.**

| Surface | Finding |
| --- | --- |
| The shim | Its only DOM id is a static `id="frame"`, inside each iframe's **own document**. Two hosts are two isolated documents. |
| The React widget host | The widget `id` is a React `key` prop (reconciliation, never rendered) and an event-routing label. No `data-widget` attributes exist. |
| Chrome / sidebar CSS | Targets Streamlit's `data-testid`s and `[data-lex-account]`. Nothing key-derived. |

No stylesheet in either repo targets a widget id or a host key. The CSS-regression risk
that framed this issue is not present, which makes the work smaller and safer than the
issue assumed — and "verified by rendering, not by reading" becomes a confirmation
step rather than the main event.

This matters more now than it did before: the flat form multiplies hosts on a page, so
had the risk been real, it would have been made worse by Problem 1's fix.

### The two real bugs, which the issue did not name

**Two `lex_widgets()` blocks share one state slot.** `key=None` falls back to the
literal `"lex_widget_host"`, so both blocks read and write the same `session_state`
entry, and the second sees the first's events. This is state corruption, not
ergonomics, and it is what an author hits the first time they put two blocks on a page.
The flat form would inherit it immediately and at higher volume.

**Widget ids shift between reruns.** `id=None` produces positional `w1, w2, …` from a
counter. A conditionally-rendered widget renumbers every widget after it, so a status
envelope stored against `w2` on one run is delivered elsewhere on the next.

### The mechanism — call-site identity

A Streamlit key has two requirements that pull against each other: it must be
**identical across reruns** (or state does not persist) and **distinct between blocks**
(or they collide). `(filename, line number, occurrence-within-run)` satisfies both. The
same line yields the same key every rerun; two lines never collide; a loop over one
line gets a stable occurrence index because the loop re-runs the same way.

This is also what makes the flat form viable without an author-supplied key, since a
flat call carries no natural name to key on.

An explicitly supplied key is kept inside the generated one — `lex_widgets_myrun_a3f1`
— so LEX-709's "a supplied key is still traceable" holds.

Widget sub-ids move from position to content: `(type, model, pk)` plus an occurrence
counter for genuine duplicates.

---

## Problem 3 — the two log surfaces do not say what they are

`calculation_log` is the **live stream**; `calculation_log_tree` is the **consolidated
tree of a finished run**. Nothing in either name carries that, and promoting both to
flat functions makes the names more prominent, not less.

**OPEN — needs a decision.** Three candidate pairs were rejected. The recommendation
below stands only until a preference is given:

- `lex_calculation_log_live()` / `lex_calculation_log_tree()`

Whatever is chosen applies to both the flat function and the block method, and the
current method names remain as aliases that warn.

---

## Phases

Each phase ships independently and leaves the API working.

**1 — Fix the shared state slot.** Replace the `"lex_widget_host"` literal with a
call-site-derived key.
*Acceptance:* two keyless `lex_widgets()` blocks on one page hold independent state
across a rerun; two blocks given the *same* explicit key also stay independent.

**2 — Make sub-ids content-derived.** Replace the positional counter.
*Acceptance:* a widget behind an `if` does not change the id of any widget after it; a
status envelope reaches the widget that produced it across a rerun in which the
condition flipped.

**3 — Add the flat `lex_*` functions**, and export the family from
`lex.lex_app.streamlit`.
*Acceptance:* `lex_calculation(...)` renders and returns the same envelope the block
form returns; the block form is unchanged in behaviour; every public name imports from
the package root.

**4 — Rename the log surfaces, with warning aliases.** Blocked on the open decision.
*Acceptance:* old names still run and print what to change.

**5 — Docs.** One page stating the rule that decides which family a future surface
belongs to, showing the flat and block shapes side by side. LEX-708's first acceptance
criterion.

**6 — Confirm the styling, by rendering.** Two blocks, several flat widgets, and the
sidebar chrome, looked at in a browser. The desk check says nothing should move; this
is the step that earns the right to say so.

Phases 1 and 2 are the state-corruption bugs and do not depend on any open decision.

---

## What is deliberately not in scope

Renaming `lex_view`, and any change to its signature or behaviour. Most existing
dashboards are built from it, and this work should not put them at risk to tidy a name.
