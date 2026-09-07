"""Reference Streamlit dashboard — copy this to ``<your_repo>/_streamlit_structure.py``.

HOW IT IS LOADED. ``lex/streamlit_app.py`` does, in effect::

    import <your_repo>._streamlit_structure as streamlit_structure
    streamlit_structure.main()

Two consequences worth knowing before anything else:

* The file is **imported** at startup and ``main()`` is called later, from
  inside the Streamlit script run. Every ``st.*`` call must therefore live
  inside a function. Anything at module level runs during import with no
  ScriptRunContext and renders nothing -- that is what "missing
  ScriptRunContext" in the startup log means.
* ``main()`` is the only name the framework looks for. Everything else here is
  this example's own organisation.

WHICH SHAPE TO REACH FOR. There are three entry points and the choice is made by
what you are embedding, not by how it is configured:

===========================  ===========================================
``lex_view(path)``           one lex-app **route** -- a table, a form, a
                             record page
``lex_calculation(...)``     one lex-app **control**, and its siblings
                             ``lex_calculation_log`` /
                             ``lex_calculation_log_tree``
``with lex_widgets() as p``  **several controls** sharing one iframe
===========================  ===========================================

A flat ``lex_*`` call is always exactly one thing. The block is the optimisation
you reach for once a page has several: each embed is a full React runtime -- its
own bundle parse, auth handshake and react-admin mount -- so five flat calls are
five of those, while a block of five is one.

None of them needs a ``key``. Keys are derived from the call site, so two blocks
never share state by accident and a loop gets one key per iteration. Pass one
only when you want a specific block findable in a session-state dump.
"""

import streamlit as st

from lex.lex_app.streamlit import (
    STAY,
    Flow,
    lex_calculation,
    lex_view,
    lex_widgets,
)

# ── Adjust these to records that exist in your project ─────────────────────
#
# A resource name is the lowercased model class name. An unknown pk renders THAT
# widget as an error card and leaves the others working, which is deliberate --
# one bad id should not blank a dashboard.
REPORT = ("salesreport", 1)
FORECAST = ("forecastrun", 1)

# Fields shown beside the Calculate control, drawn by the product's own
# FieldView -- so a foreign key arrives as its display name and a datetime is
# formatted the way the grid formats it. No second formatting path to drift.
# An unknown name is skipped rather than rendered as a blank slot.
REPORT_FIELDS = ["period", "created_at"]


def one_control() -> None:
    """The smallest useful thing: a Calculate button with its status.

    One widget, so one flat call. It reads like ``lex_view("salesreport")``
    because it is the same idea -- embed exactly one thing.
    """
    st.header("Sales report")
    st.caption("Press Calculate and watch the status change in place.")

    model, pk = REPORT
    lex_calculation(model, pk=pk, title="Sales report", fields=REPORT_FIELDS)


def several_controls() -> None:
    """Three controls, one React runtime — what a real dashboard looks like.

    Written as three flat calls this would be three iframes, three bundles and
    three auth handshakes. The block buys one runtime for the price of a single
    constraint: the widgets appear where the block CLOSES, not where each call
    sits.

    This is the shape to copy. Widget count is free; block count is not.
    """
    st.header("Month end")

    with lex_widgets() as page:
        page.calculation(REPORT[0], pk=REPORT[1], title="Sales report")
        page.calculation(FORECAST[0], pk=FORECAST[1], title="Forecast")
        page.calculation(REPORT[0], pk=REPORT[1], title="Reconciliation", variant="status")


def log_with_room() -> None:
    """A control and its log, sized separately.

    ``calculation(..., show_log=True)`` puts the log inside the widget, which is
    fine for a glance and cramped for reading: the log wants width and height
    while the control wants a line. Declaring them separately is what makes the
    log readable, and both still share the one runtime.
    """
    st.header("Execution log")

    model, pk = REPORT
    with lex_widgets() as page:
        page.calculation(model, pk=pk)
        # The LIVE stream -- what you want while something is running.
        page.calculation_log(model, pk=pk, height=700)


def composing_a_row() -> None:
    """Absence means hidden, so you add what a layout needs.

    ``variant`` maps onto the product's own control, which already draws all
    three forms. Each of these is one widget, so each is one flat call -- no
    block, no key.
    """
    st.header("Composing a row")
    model, pk = REPORT

    st.markdown("**Button only** — an action bar, nothing to read")
    lex_calculation(model, pk=pk, variant="action", show_log_button=False)

    st.markdown("**Status only** — a monitoring strip, nothing to press")
    lex_calculation(model, pk=pk, variant="status", show_log_button=False)

    st.markdown("**Beside your own content** — constrain it with `st.columns`")
    # A custom component is an iframe, and Streamlit gives every component a
    # full-width block. A bare button still spans the page unless you constrain
    # it the way you would any Streamlit element.
    button_col, text_col = st.columns([1, 5])
    with button_col:
        lex_calculation(model, pk=pk, variant="action", show_log_button=False)
    with text_col:
        st.write("Your own Streamlit content, sitting beside the button.")


def reading_the_result() -> None:
    """``on_status=True`` opts a widget into reporting back to Python.

    Without it the call returns ``None`` and no event is emitted, so the common
    display-only case costs nothing.

    The value arrives on the NEXT rerun. That is the contract every Streamlit
    input widget has -- Streamlit re-executes top-to-bottom on each event -- and
    it is why this reads ``status`` rather than waiting on anything.
    """
    st.header("Branching on the outcome")

    model, pk = REPORT
    status = lex_calculation(
        model, pk=pk, title="Sales report", fields=REPORT_FIELDS, on_status=True
    )

    if not status:
        st.caption("Run the calculation to see its result reported back to Python.")
        return

    state = status["payload"]["status"]
    if state == "SUCCESS":
        st.success("Finished — downstream reports can be built now.")
    elif state == "ERROR":
        st.error("Failed. Open the log for the failing step.")
    else:
        st.info(f"Currently {state}.")


def a_whole_page() -> None:
    """``lex_view`` embeds a lex-app ROUTE, chrome removed.

    The same table your users see in the app, inside this page. Use it when you
    want the real grid -- filters, sorting, export -- rather than a Streamlit
    re-implementation of one.
    """
    st.header("The records themselves")
    lex_view(REPORT[0], height=600, hide_toolbar=False)


def a_multi_step_flow() -> None:
    """Chain forms together: create one record, land on the next.

    A ``Flow`` says where to go after a save. ``{id}`` is the record just
    written, so "create a report, then edit the forecast it belongs to" is one
    rule rather than a callback.

    Rules are checked when written. A mistyped operation raises here, at the
    line you wrote, instead of being serialised into the URL and quietly
    matching nothing in the browser.

    ``STAY`` keeps the user on the form and clears it -- the shape you want for
    entering several records in a row.
    """
    st.header("Guided entry")
    st.caption("Save a report and land on the forecast; keep adding forecasts in place.")

    flow = (
        Flow()
        .after_create(REPORT[0], f"/{FORECAST[0]}/create")
        .after_save(FORECAST[0], STAY)
    )

    lex_view(f"{REPORT[0]}/create", height=700, flow=flow)


#: Sections, grouped the way lex-app groups its own sidenav. ``st.navigation``
#: takes a mapping of header -> pages and renders the headers, so the grouping
#: is data rather than layout code.
SECTIONS = {
    "Controls": [
        (one_control, "One control", ":material/widgets:"),
        (composing_a_row, "Composing a row", ":material/view_column:"),
        (several_controls, "Month end", ":material/dashboard:"),
    ],
    "Logs": [
        (log_with_room, "Execution log", ":material/description:"),
    ],
    "Python": [
        (reading_the_result, "Branching on the outcome", ":material/function:"),
    ],
    "Pages": [
        (a_whole_page, "The records themselves", ":material/table:"),
        (a_multi_step_flow, "Guided entry", ":material/linear_scale:"),
    ],
}


def main() -> None:
    """The entry point ``lex/streamlit_app.py`` calls.

    ONE SECTION AT A TIME, and that is the point rather than a convenience.
    Every embed is a full React runtime. This file exists to show each shape
    side by side, which is several of them; rendering them all together would
    make the page slower than any real dashboard should be, and the slowness
    would be this example's fault rather than the widgets'.

    ``st.navigation`` renders into the sidebar's navigation slot -- section
    headers, icons, the active item highlighted, a URL per page. lex-app draws
    its logo and identity above it and the log-out row beneath, so a dashboard
    that uses real navigation sits correctly between them.
    """
    pages = {
        header: [
            st.Page(render, title=title, icon=icon, url_path=render.__name__)
            for render, title, icon in entries
        ]
        for header, entries in SECTIONS.items()
    }
    st.navigation(pages).run()
