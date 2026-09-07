"""Intent: exactly one feedback launcher on screen, owned by the top-level page.

lex-app already settled the rule in index.html, after both failure modes had
happened in production: a Streamlit dashboard with N embedded widgets showed N
stacked launchers, each costing its own `/api/quackback-widget-token` request;
and a Streamlit page framed by lex-app stacked a second launcher over the host's.
The rule that fixes both is one line — the top-level document owns the launcher.

This file covers the third case, which nothing owned: a Streamlit page that is
NOT framed is a top-level document, and had no launcher at all, because
lex-app's copy lives in the React app and that page is not it.

The scenario that earns the file is 1.332. A Streamlit custom component is
ITSELF an iframe, so the obvious `window.self !== window.top` check is
trivially true here and would disable the launcher everywhere, forever, with no
error. The question has to be asked about the PARENT.

Cluster 01-init, batch 1am, scenarios 1.331-1.335.

Run:
    python -m lex pytest lex/test_project/tests/init/test_1am_quackback_launcher.py
"""

import pytest

from lex.lex_app.streamlit.quackback import (
    QUACKBACK_SDK_URL,
    quackback_enabled,
    quackback_launcher_js,
)

pytestmark = pytest.mark.init

BASE = "https://app.example.test"


def _code_only(js: str) -> str:
    """The script with its `//` comments removed.

    Asserting against raw source means an assertion can pass -- or fail -- on
    prose. This file's own explanation of why it does NOT test
    `window.top !== window` contains that exact string, so 1.332 failed on the
    comment defending the behaviour it was checking.
    """
    return "\n".join(
        line.split("//", 1)[0] for line in js.split("\n")
    )


class TestCluster1am_QuackbackLauncher:
    """The launcher script, and the conditions it refuses to mount under."""

    def test_01_331_mounts_the_sdk_on_the_host_page(self) -> None:
        """Scenario 1.331: the script loads the widget SDK into the host document.

        Given a Streamlit page that is not framed
        When the launcher script is built
        Then it appends the SDK to the PARENT document, not its own

        Anything drawn inside a component iframe is trapped in it — and in a
        zero-height one at that, so it would never be seen.
        """
        js = quackback_launcher_js(BASE)

        assert QUACKBACK_SDK_URL in js
        assert "doc.head.appendChild(s)" in js
        assert "var doc = host.document" in js

    def test_01_332_asks_whether_the_PARENT_is_framed(self) -> None:
        """Scenario 1.332: the frame check looks two levels up.

        Given this script always runs inside a component iframe
        When it decides whether to mount
        Then it tests `host.top !== host`, never `window.top !== window`

        Testing itself would answer "framed" on every page — the launcher would
        silently never appear, which is indistinguishable from it being broken.
        """
        code = _code_only(quackback_launcher_js(BASE))

        assert "host.top !== host" in code
        assert "window.top !== window" not in code

    def test_01_333_a_framed_page_mounts_nothing(self) -> None:
        """Scenario 1.333: when framed, the script returns before any work.

        Given a Streamlit page inside lex-app
        When the launcher runs
        Then it exits before creating a script or POSTing for a token

        lex-app owns the launcher there. A second one is both a duplicate
        bubble and a duplicate token request per page load.
        """
        js = quackback_launcher_js(BASE)

        guard = js.index("if (framed) {")
        assert guard < js.index("doc.createElement('script')")
        assert guard < js.index("/api/quackback-widget-token")
        # A cross-origin parent cannot be inspected, and that failure means
        # framed — the safe direction, since the cost of guessing wrong is a
        # duplicate launcher rather than a missing one.
        assert "catch (e) { framed = true; }" in js

    def test_01_334_survives_streamlit_rerunning_the_script(self) -> None:
        """Scenario 1.334: a rerun does not add a second launcher.

        Given Streamlit re-executes the whole script on every interaction
        When the launcher script runs again
        Then a marker on the host window makes it a no-op

        Without this, a page would accumulate one SDK script per click.
        """
        js = quackback_launcher_js(BASE)

        assert "if (host.__lexQuackbackLoaded) return" in js
        assert "host.__lexQuackbackLoaded = true" in js

    def test_01_335_identifies_against_lex_app_not_streamlit(self) -> None:
        """Scenario 1.335: the token URL is absolute, against lex-app.

        Given the Streamlit page is not served from lex-app's origin
        When the identify call is built
        Then it targets lex-app's absolute URL with credentials

        A relative "/api/..." resolves against Streamlit and 404s, which would
        leave every launcher anonymous with nothing obviously wrong.
        """
        js = quackback_launcher_js(BASE)

        assert f"{BASE}/api/quackback-widget-token" in js
        assert "credentials: 'include'" in js

    def test_01_335b_an_explicit_opt_out_produces_no_script(self, monkeypatch) -> None:
        """Scenario 1.335b: LEX_STREAMLIT_QUACKBACK=0 disables it entirely."""
        monkeypatch.setenv("LEX_STREAMLIT_QUACKBACK", "0")

        assert quackback_enabled() is False
        assert quackback_launcher_js(BASE) == ""
