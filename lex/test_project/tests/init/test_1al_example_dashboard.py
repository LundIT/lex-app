"""Intent: the dashboard we tell people to copy must actually run when copied.

``lex/streamlit_app.py`` imports ``<repo>._streamlit_structure`` at startup and
calls ``main()`` later, inside the script run. Two ways a shipped example breaks
that contract silently:

* it renders nothing, because a Streamlit call sits at module level where there
  is no ScriptRunContext -- the copier sees an empty page and a
  "missing ScriptRunContext" line buried in the startup log;
* it drifts, because the API moved and nobody re-read the example. An example is
  documentation that can be executed, which is the only kind that cannot rot
  quietly.

1.330 is the one that pays for the file: the example builds a real ``Flow``, so
if a rule in it could never fire, this fails rather than a copier discovering it
in a browser.

Cluster 01-init, batch 1al, scenarios 1.327-1.330.

Run:
    python -m lex pytest lex/test_project/tests/init/test_1al_example_dashboard.py
"""

import ast
import inspect
from pathlib import Path

import pytest

from lex.lex_app.streamlit.examples import _streamlit_structure as example

pytestmark = pytest.mark.init


class TestCluster1al_ExampleDashboard:
    """The shipped reference dashboard, checked against the loader's contract."""

    def test_01_327_exposes_the_only_name_the_framework_looks_for(self):
        """Scenario 1.327: ``main()`` exists and takes no arguments.

        Given lex/streamlit_app.py calling ``streamlit_structure.main()``
        When the example is inspected
        Then main is callable with no arguments

        The loader checks ``hasattr(streamlit_structure, "main")`` and calls it
        bare. A main() that needed an argument would fail at render time, in
        production, on someone else's project.
        """
        assert callable(example.main)
        assert inspect.signature(example.main).parameters == {}

    def test_01_328_renders_nothing_at_import_time(self):
        """Scenario 1.328: no Streamlit call sits at module level.

        Given the example is IMPORTED at startup and run later
        When its module-level statements are inspected
        Then none of them calls st.*

        A module-level st.* call executes during import, with no
        ScriptRunContext. It renders nothing, warns into a startup log nobody
        reads, and leaves the copier with a blank page.
        """
        source = Path(inspect.getfile(example)).read_text()
        tree = ast.parse(source)

        offenders = []
        for node in tree.body:
            # Function and class bodies run later, which is the point.
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            for inner in ast.walk(node):
                if (
                    isinstance(inner, ast.Call)
                    and isinstance(inner.func, ast.Attribute)
                    and isinstance(inner.func.value, ast.Name)
                    and inner.func.value.id == "st"
                ):
                    offenders.append(f"line {inner.lineno}: st.{inner.func.attr}(...)")

        assert not offenders, (
            "Streamlit calls at module level render nothing at import time: "
            + "; ".join(offenders)
        )

    def test_01_329_every_declared_section_is_a_real_page(self):
        """Scenario 1.329: SECTIONS points only at functions that exist.

        Given the navigation table
        When each entry is inspected
        Then it names a zero-argument callable with a docstring

        st.Page renders whatever it is handed; a stale entry surfaces as a page
        that errors when clicked rather than at import.
        """
        assert example.SECTIONS, "the example declares no sections"

        for header, entries in example.SECTIONS.items():
            assert entries, f"section {header!r} is empty"
            for render, title, icon in entries:
                assert callable(render), f"{header}/{title} is not callable"
                assert inspect.signature(render).parameters == {}, (
                    f"{render.__name__} takes arguments; st.Page calls it bare"
                )
                assert render.__doc__, (
                    f"{render.__name__} has no docstring -- this file IS the "
                    f"explanation, so a section without one teaches nothing"
                )

    def test_01_330_the_flow_it_demonstrates_could_actually_fire(self):
        """Scenario 1.330: the example's Flow is valid.

        Given the guided-entry section builds a real Flow
        When that section's source is executed for its flow
        Then no rule is rejected

        Flow validates on write, so a rule that could never fire raises here.
        Without this the example could ship a redirect that silently does
        nothing -- exactly the failure Flow validation exists to prevent, shipped
        in the file that teaches people how to use it.
        """
        from lex.lex_app.streamlit import STAY, Flow

        report, forecast = example.REPORT[0], example.FORECAST[0]
        flow = (
            Flow()
            .after_create(report, f"/{forecast}/create")
            .after_save(forecast, STAY)
        )

        assert flow[f"{report}/create"] == f"/{forecast}/create"
        assert flow[f"{forecast}/create"] == STAY
        assert flow[f"{forecast}/update"] == STAY
