"""Embeddable lex-app widgets for Streamlit pages.

Two shapes, and which one to reach for is decided by how many widgets you want,
not by what they are:

* a flat ``lex_*`` function embeds **exactly one** widget, the way ``lex_view``
  embeds exactly one route;
* ``lex_widgets()`` embeds **several** into one iframe, so widget count costs
  manifest entries rather than React runtimes.

::

    lex_calculation("navcalc", pk=1, variant="action")

    with lex_widgets() as page:
        page.calculation("navcalc", pk=1)
        page.calculation_log_tree("navcalc", pk=1)
"""

from lex.lex_app.streamlit.widgets.host import (
    WidgetPage,
    lex_calculation,
    lex_calculation_log,
    lex_calculation_log_tree,
    lex_widgets,
)
from lex.lex_app.streamlit.widgets.keys import widget_key
from lex.lex_app.streamlit.widgets.spec import (
    MANIFEST_VERSION,
    WidgetSpecError,
    build_manifest,
    calculation_spec,
)

__all__ = [
    "MANIFEST_VERSION",
    "WidgetPage",
    "WidgetSpecError",
    "build_manifest",
    "calculation_spec",
    "lex_calculation",
    "lex_calculation_log",
    "lex_calculation_log_tree",
    "lex_widgets",
    "widget_key",
]
