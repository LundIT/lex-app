"""Intent: two widget blocks on one page must not read each other's events, and
a redirect rule that can never fire must say so when it is written.

Both failures this file prevents are silent ones.

A ``lex_widgets()`` block used to key its component on the literal
``"lex_widget_host"``. Two blocks on a page therefore shared one
``session_state`` slot: the second read the first's events, and nothing
anywhere said so. Widget ids had the same shape of problem from the other
direction -- they were positional (``w1``, ``w2``, ...), so a widget rendered
behind an ``if`` renumbered every widget after it, and on the rerun where that
condition flipped a status envelope arrived at the wrong widget.

A ``Flow`` rule with a mistyped operation was accepted, serialised into the URL,
shipped to the browser, and then matched nothing. No error, no redirect, no
explanation -- the button simply did not navigate.

Cluster 01-init, batch 1ak, scenarios 1.316-1.326.

Run:
    python -m lex pytest lex/test_project/tests/init/test_1ak_widget_keys_and_flow.py
"""

import pytest

from lex.lex_app.streamlit import STAY, Flow, FlowError
from lex.lex_app.streamlit.widgets.host import WidgetPage
from lex.lex_app.streamlit.widgets.keys import widget_key

pytestmark = pytest.mark.init


class TestCluster1ak_WidgetKeys:
    """Keys that are unique without the author having chosen them."""

    def test_01_316_two_blocks_on_different_lines_do_not_share_a_slot(self):
        """Scenario 1.316: two keyless blocks get different keys.

        Given two ``lex_widgets()`` blocks on separate source lines
        When each derives its component key
        Then the keys differ, so neither reads the other's session_state
        """
        first = widget_key("lex_widgets", None)
        second = widget_key("lex_widgets", None)

        assert first != second, (
            "two keyless blocks collided -- they would share one session_state "
            "slot and the second would see the first's events"
        )

    def test_01_317_the_same_line_yields_the_same_key_every_run(self):
        """Scenario 1.317: a key is stable across reruns.

        Given the same source line evaluated on two script runs
        When the key is derived each time
        Then it is identical, so the component keeps its state

        The counterpart to 1.316 and the reason the key cannot simply be a
        counter: Streamlit drops the state of a component whose key changed.
        """

        def one_run():
            return widget_key("lex_widgets", None)

        assert one_run() == one_run()

    def test_01_318_a_loop_over_one_line_gets_one_key_per_iteration(self):
        """Scenario 1.318: content discriminates iterations.

        Given ``for pk in (1, 2, 3): lex_calculation("navcalc", pk=pk)``
        When each call derives a key from the same source line
        Then the three keys differ, because the pk is folded in

        Call-site identity alone cannot separate these -- every iteration is the
        same line. This is why the flat helpers pass model and pk.
        """

        def row(pk):
            return widget_key("lex_widgets", None, parts=("calculation", "navcalc", pk))

        keys = [row(pk) for pk in (1, 2, 3)]
        assert len(set(keys)) == 3
        assert keys == [row(pk) for pk in (1, 2, 3)], "not reproducible on rerun"

    def test_01_319_an_author_supplied_key_stays_findable(self):
        """Scenario 1.319: an explicit key survives into the generated one.

        Given ``lex_widgets(key="myrun")``
        When the component key is derived
        Then "myrun" appears in it, so the block is greppable in a state dump
        """
        assert "myrun" in widget_key("lex_widgets", "myrun")

    def test_01_320_hiding_a_widget_does_not_renumber_the_others(self):
        """Scenario 1.320: sub-ids come from content, not position.

        Given a page whose second widget is behind a condition
        When that condition flips between runs
        Then every other widget keeps the id it had

        With positional ids this was the bug: the third widget was ``w3`` on one
        run and ``w2`` on the next, so a status envelope addressed to ``w3``
        was delivered to whatever now held that id.
        """

        def ids(show_middle: bool):
            page = WidgetPage()
            page.calculation("navcalc", 1)
            if show_middle:
                page.calculation("navcalc", 2)
            page.calculation("navcalc", 3)
            return [spec["id"] for spec in page._specs]

        with_middle = ids(True)
        without = ids(False)

        assert with_middle[0] == without[0]
        assert with_middle[-1] == without[-1], (
            f"the last widget was renamed when a sibling was hidden: "
            f"{with_middle[-1]!r} became {without[-1]!r}"
        )

    def test_01_321_a_genuine_duplicate_still_gets_its_own_id(self):
        """Scenario 1.321: the same model and pk twice do not collide.

        Given two calculation widgets for the same record on one page
        When ids are assigned
        Then they differ, because build_manifest refuses duplicate ids
        """
        page = WidgetPage()
        page.calculation("navcalc", 1)
        page.calculation("navcalc", 1)

        ids = [spec["id"] for spec in page._specs]
        assert len(set(ids)) == 2, f"duplicate widget ids: {ids}"

    def test_01_322_an_explicit_id_is_left_alone(self):
        """Scenario 1.322: a chosen id is used verbatim.

        Given ``page.calculation(..., id="nav")``
        When the spec is built
        Then the id is exactly "nav" -- events addressed to it stay addressable
        """
        page = WidgetPage()
        page.calculation("navcalc", 1, id="nav")
        assert page._specs[0]["id"] == "nav"


class TestCluster1ak_Flow:
    """A redirect rule that cannot fire fails where it was written."""

    def test_01_323_a_mistyped_operation_is_refused(self):
        """Scenario 1.323: "creat" raises instead of silently never matching.

        Given a flow rule whose operation is misspelled
        When the Flow is built
        Then FlowError names the mistake and the valid operations
        """
        with pytest.raises(FlowError) as caught:
            Flow({"investor/creat": "/cashflow"})

        assert "creat" in str(caught.value)
        assert "create" in str(caught.value)

    def test_01_324_a_delete_rule_explains_why_it_cannot_work(self):
        """Scenario 1.324: delete is refused with the reason.

        Given ``"investor/delete"``
        When the Flow is built
        Then the error says the app emits a delete event but never navigates

        The app has no delete-redirect resolver. Accepting the rule would ship
        it to the browser to be ignored, which is the failure this whole batch
        exists to remove.
        """
        with pytest.raises(FlowError) as caught:
            Flow().after_create("investor", "/x").update({"investor/delete": "/y"})

        assert "delete" in str(caught.value).lower()

    def test_01_325_every_way_of_writing_a_rule_is_checked(self):
        """Scenario 1.325: validation cannot be bypassed by another door.

        Given the constructor, item assignment, update() and setdefault()
        When a bad rule is written through each
        Then all four raise

        Flow subclasses dict, so a check on only the builders would leave three
        unguarded ways to put a rule in.
        """
        bad = "investor/destroy"

        with pytest.raises(FlowError):
            Flow({bad: "/x"})

        flow = Flow()
        with pytest.raises(FlowError):
            flow[bad] = "/x"
        with pytest.raises(FlowError):
            flow.update({bad: "/x"})
        with pytest.raises(FlowError):
            flow.setdefault(bad, "/x")

        assert dict(flow) == {}, "a rejected rule was stored anyway"

    def test_01_326_after_save_writes_both_halves(self):
        """Scenario 1.326: one call covers create and update.

        Given ``after_save("cashflow", STAY)``
        When the flow is inspected
        Then both rules are present with the same target

        Writing the pair by hand is where the two drift apart.
        """
        flow = Flow().after_save("cashflow", STAY)

        assert flow == {"cashflow/create": STAY, "cashflow/update": STAY}
