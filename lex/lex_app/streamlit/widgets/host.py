"""``lex_widgets()`` -- put calculations on a Streamlit page, one runtime for all.

    with lex_widgets() as page:
        status = page.calculation("quarter", pk=42, show_log=True, on_status=True)
        page.calculation("quarter", pk=43)

    if status and status["status"] == "SUCCESS":
        st.dataframe(load_results())

Everything inside the block is collected, and the host iframe renders **once**
when the block closes. That is the whole point: a dashboard of thirteen
calculations is thirteen widgets in one React runtime, not thirteen iframes with
a React bundle, a JS context and four WebSockets each.

The cost, stated plainly: widgets appear where the ``with`` block closes, not
where each call sits. Interleaving ``st.write()`` between two widgets is not
available. The context manager makes that boundary a language construct rather
than a convention someone has to remember.

PERFORMANCE — the one number that matters
-----------------------------------------
**Widget count is free. Block count is not.**

Each ``lex_widgets()`` block is one iframe, and each iframe is a full React
application: its own bundle parse, its own auth handshake, its own ``model_info``
fetch, its own react-admin mount. Ten widgets in one block boot one app. Ten
blocks boot ten, they contend for the same network and main thread, and a page
scrolled during that window shows widgets still coming up -- which reads as
lazy loading and is not. The frames all start loading immediately; they simply
have a lot to do.

So prefer::

    with lex_widgets() as page:          # one runtime, ten widgets
        for pk in pks:
            page.calculation("navcalc", pk=pk)

over a block per widget. Reach for a second block only when a layout genuinely
needs Streamlit content between two groups -- that is a real reason, and it
costs a runtime.
"""

from __future__ import annotations

import urllib.parse
from typing import Any, Dict, List, Optional, Tuple

from lex.lex_app.streamlit._widget_host_component import render_widget_host
from lex.streamlit_theme import THEME_STORAGE_KEY
from lex.lex_app.streamlit.embed import _resolve_base_url
from lex.lex_app.streamlit.widgets.keys import widget_key
from lex.lex_app.streamlit.widgets.spec import (
    PK,
    build_manifest,
    calculation_log_spec,
    calculation_spec,
)

#: Route on the lex-app frontend that renders a manifest.
#: The widget host page. A real file in the SPA build, not an app route.
#:
#: ``/embed/widgets`` still works and renders the same widgets, but it is served
#: by index.html — the admin app's entry, which imports ag-grid at module scope
#: and declares every Resource, so a Calculate button costs ~6 MB of JS to parse.
#: embed.html is a second Vite entry that mounts the widgets in <AdminContext>
#: alone: measured 1563 KB raw / 517 KB gzipped against 6281 / 1895, a 75% cut,
#: paid once per frame and there are N frames on a dashboard.
#:
#: Served without a URL route because ``serve_react`` returns any file that
#: exists before falling back to the SPA shell.
HOST_PATH = "/embed.html"

#: Height for the log inside the page-level dialog. Generous on purpose -- the
#: whole reason the dialog exists is that the log is unreadable when it is
#: bounded by a widget's box rather than by the browser window.
_DIALOG_LOG_HEIGHT = 820


class WidgetPage:
    """Collects widget specs inside a ``lex_widgets()`` block.

    Not constructed directly -- ``lex_widgets()`` yields one.
    """

    def __init__(self) -> None:
        self._specs: List[Dict[str, Any]] = []
        self._result: Optional[dict] = None
        # Counts how many times an identical (kind, model, pk) has been added,
        # so genuine duplicates still get distinct ids.
        self._seen: Dict[str, int] = {}

    def _next_id(self, explicit: Optional[str], kind: str, model: str, pk: PK) -> str:
        """An id that survives a widget above it being hidden.

        Ids used to be positional -- ``w1``, ``w2``, ... from a running counter --
        which meant a widget rendered behind an ``if`` renumbered every widget
        after it. Status envelopes are routed back BY id, so on the rerun where
        that condition flipped, an envelope reached the wrong widget.

        Deriving from what the widget is about instead means hiding one widget
        leaves its siblings' ids untouched.
        """
        if explicit:
            return explicit
        base = f"{kind}_{model}_{pk}"
        count = self._seen.get(base, 0)
        self._seen[base] = count + 1
        # First one keeps the clean name; only a real duplicate is suffixed, so
        # the common case stays readable in an event payload.
        return base if count == 0 else f"{base}__{count}"

    def calculation(
        self,
        model: str,
        pk: PK,
        *,
        show_log: bool = False,
        log_height: Optional[int] = None,
        on_status: bool = False,
        title: Optional[str] = None,
        fields: Optional[List[str]] = None,
        variant: str = "full",
        show_log_button: bool = True,
        id: Optional[str] = None,
    ) -> Optional[dict]:
        """Add a calculation widget: the Calculate control, its status, its log.

        Composable: **absence means hidden**, so the default is minimal and you
        add only what a given layout needs.

        * ``variant`` -- ``"full"`` (pill + button), ``"status"`` (pill alone) or
          ``"action"`` (button alone). Passed straight to the product's own
          control, which already draws these three.
        * ``title`` -- a heading. Omit it and no heading renders.
        * ``fields`` -- record fields beside the control, drawn by the product's
          FieldView so an FK shows its display name and a datetime is formatted
          as the grid formats it. Omit for none.
        * ``show_log_button`` -- the control that opens the live log popup.

        Just the button::

            page.calculation("navcalc", pk=1, variant="action", show_log_button=False)

        Status only, for a compact strip::

            page.calculation("navcalc", pk=1, variant="status", show_log_button=False)

        Returns the latest status envelope when ``on_status=True``, else
        ``None``. The value is from the *previous* run of the script, because
        Streamlit reruns top-to-bottom on each event -- the same contract every
        Streamlit input widget has.
        """
        widget_id = self._next_id(id, "calculation", model, pk)
        self._specs.append(
            calculation_spec(
                widget_id,
                model,
                pk,
                show_log=show_log,
                log_height=log_height,
                on_status=on_status,
                title=title,
                fields=fields,
                variant=variant,
                show_log_button=show_log_button,
            )
        )
        # Route the stored envelope back to the widget that produced it, so two
        # widgets on a page do not read each other's status.
        #
        # The type check is load-bearing, not defensive noise: every envelope
        # type shares one component value, so an `open_log` click for THIS
        # widget would otherwise be handed back as if it were a status. Its
        # payload has no "status" key, so the caller's
        # ``status["payload"]["status"]`` raised KeyError.
        result = self._result
        if (
            isinstance(result, dict)
            and result.get("type") == "calculation_status"
            and (result.get("payload") or {}).get("widget_id") == widget_id
        ):
            return result
        return None

    def calculation_log(
        self,
        model: str,
        pk: PK,
        *,
        height: Optional[int] = None,
        calculation_id: Optional[str] = None,
        id: Optional[str] = None,
    ) -> None:
        """Add the live calculation log on its own, sized by you.

        Prefer this over ``calculation(..., show_log=True)`` when the log is
        the point. A two-pane tree wants width and height; a Calculate control
        wants a line. Declaring them separately lets the control sit in a
        narrow column and the log run full width beneath it -- which is what
        makes the log readable rather than a letterbox.

        Returns ``None``: a log emits no status. Use ``calculation(...)`` for
        that.
        """
        self._specs.append(
            calculation_log_spec(
                self._next_id(id, "calculation_log", model, pk),
                model,
                pk,
                height=height,
                calculation_id=calculation_id,
            )
        )
        return None

    def calculation_log_tree(
        self,
        model: str,
        pk: PK,
        *,
        height: Optional[int] = None,
        calculation_id: Optional[str] = None,
        id: Optional[str] = None,
    ) -> None:
        """Add the log's execution TREE rather than its live stream.

        A different question: the stream shows what is happening now, the tree
        shows how a finished run was structured. Prefer ``calculation_log`` for
        watching; reach for this when navigating a completed run.
        """
        self._specs.append(
            calculation_log_spec(
                self._next_id(id, "calculation_log_tree", model, pk),
                model,
                pk,
                height=height,
                calculation_id=calculation_id,
                tree=True,
            )
        )
        return None

    # ── internals ───────────────────────────────────────────────────────
    def _manifest(self) -> Dict[str, Any]:
        return build_manifest(self._specs)

    def _is_empty(self) -> bool:
        return not self._specs


class _LexWidgets:
    """Context manager returned by :func:`lex_widgets`."""

    def __init__(
        self,
        *,
        key: Optional[str],
        min_height: int,
        key_parts: Tuple[Any, ...] = (),
        key_depth: int = 0,
    ) -> None:  # noqa: D107
        self._key = key
        self._min_height = min_height
        self._page = WidgetPage()
        # Derived once, here, rather than in __enter__: the key must be the SAME
        # string when __enter__ reads session_state and when __exit__ renders,
        # and deriving it twice from the call stack would read two different
        # frames (this constructor's caller, then Streamlit's).
        self._component_key = widget_key(
            "lex_widgets", key, parts=key_parts, extra_depth=key_depth + 1
        )

    def __enter__(self) -> WidgetPage:
        import streamlit as st

        # Streamlit stores a keyed component's current value in session_state
        # under that key, so read it directly rather than stashing a copy of our
        # own. An earlier version kept a private key and wrote it in __exit__,
        # which meant the value was always one rerun behind what the component
        # already knew -- so the first Calculate never surfaced in Python.
        #
        # The key used to be the literal "lex_widget_host", which meant TWO
        # blocks on one page read and wrote the same slot: the second block saw
        # the first block's events. It is now derived from the call site.
        self._page._result = st.session_state.get(self._component_key)
        return self._page

    def __exit__(self, exc_type, exc, tb) -> bool:
        import streamlit as st

        # A failure inside the block is the author's, not ours -- let it
        # propagate untouched rather than rendering a half-built page.
        if exc_type is not None:
            return False

        if self._page._is_empty():
            return False

        base = _resolve_base_url()
        # embed=true is what actually strips the app chrome (sidebar, appbar,
        # breadcrumb) -- see useEmbedContext.detectEmbed. Without it the widget
        # host renders inside the full CustomLayout, which is both wrong to look
        # at and 100vh-based, so it feeds the host's content-height resize into a
        # runaway growth loop.
        url = f"{base}{HOST_PATH}?embed=true"
        parsed = urllib.parse.urlparse(base)
        expected_origin = (
            f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else None
        )

        # Streamlit keeps the returned value in session_state[key] for us; the
        # next run's __enter__ reads it there. Nothing to stash.
        render_widget_host(
            url=url,
            manifest=self._page._manifest(),
            expected_origin=expected_origin,
            min_height=self._min_height,
            theme_storage_key=THEME_STORAGE_KEY,
            key=self._component_key,
        )

        self._maybe_open_log_dialog(url, expected_origin)
        return False

    def _maybe_open_log_dialog(self, url: str, expected_origin: Optional[str]) -> None:
        """Show the log in a PAGE-LEVEL dialog when a widget asks for it.

        Why it cannot simply pop up inside the widget: the log dialog renders in
        a portal with ``position: fixed``, so inside an embedded frame it is
        clipped to that frame's viewport and does not grow ``scrollHeight`` --
        the host's content-height resize cannot rescue it. A Streamlit dialog
        lives on the page instead of in the frame, so it is bounded by the
        browser window rather than by a widget's box.

        The dialog hosts its own single-widget manifest. That reuses the whole
        rendering path rather than adding a second way to draw a log.
        """
        import streamlit as st

        event = st.session_state.get(self._component_key)
        if not isinstance(event, dict) or event.get("type") != "open_log":
            return

        payload = event.get("payload") or {}
        seen_key = f"_lex_widgets_log_seen_{self._component_key}"
        # One dialog per click. Without this the dialog reopens on every rerun,
        # because the component value persists after being consumed.
        if st.session_state.get(seen_key) == event.get("id"):
            return
        st.session_state[seen_key] = event.get("id")

        model = payload.get("model")
        pk = payload.get("pk")
        calculation_id = payload.get("calculationId") or payload.get("calculation_id")
        if not model or pk is None:
            return

        title = f"Calculation log — {model} #{pk}"

        @st.dialog(title, width="large")  # type: ignore[misc]
        def _log_dialog() -> None:
            spec = calculation_log_spec(
                "dialog_log",
                str(model),
                pk,
                height=_DIALOG_LOG_HEIGHT,
                calculation_id=calculation_id or None,
                # The popup streams -- the default for calculation_log now.
            )
            render_widget_host(
                url=url,
                manifest=build_manifest([spec]),
                expected_origin=expected_origin,
                min_height=_DIALOG_LOG_HEIGHT,
                theme_storage_key=THEME_STORAGE_KEY,
                key=f"{self._component_key}_log_dialog",
            )

        _log_dialog()


def lex_widgets(*, key: Optional[str] = None, min_height: int = 48) -> _LexWidgets:
    """Open a widget page. See the module docstring for the contract.

    ``key`` distinguishes two hosts on one page.

    ``min_height`` is only the height used *before* the host reports its real
    content height -- it is a floor, not a size. It defaults low (one control
    row) because the old 200px default made a lone button sit in a tall empty
    band until the first resize landed. Raise it only if you know a block is
    tall and want to avoid the initial reflow.

    **Width is Streamlit's, not ours.** A custom component occupies a full-width
    block, so a bare control still spans the page. Constrain it the way you
    would any Streamlit element -- put it in a column::

        narrow, rest = st.columns([1, 6])
        with narrow:
            with lex_widgets(key="run") as page:
                page.calculation("navcalc", pk=1, variant="action",
                                 show_log_button=False)
        with rest:
            st.write("... your own content, beside the button ...")
    """
    return _LexWidgets(key=key, min_height=min_height, key_depth=1)


# ---------------------------------------------------------------------------
# One widget, one call -- the shape `lex_view` already taught
# ---------------------------------------------------------------------------
#
# `lex_view(path)` embeds one lex-app route. These embed one lex-app control,
# and read the same way at the call site, so the family explains itself: a flat
# `lex_*` function embeds exactly one thing, and `lex_widgets()` embeds several
# into one frame.
#
# Each is the block form entered and exited in a single call -- NOT a second
# rendering path. There is one manifest builder, one host, one place a bug can
# live. A parallel single-widget implementation is how two entry points start
# disagreeing about what a widget is.
#
# The cost is real and worth knowing: each of these is its own iframe, so its
# own React runtime. Right for a control or two, wrong for ten -- reach for
# `lex_widgets()` once a page has several, and it pays for the block.


def _solo(method: str, model: str, pk: PK, key: Optional[str], min_height: int, kwargs):
    """Render one widget in its own host and return whatever the method returns.

    ``model`` and ``pk`` are folded into the host key so a loop over one source
    line -- ``for pk in pks: lex_calculation("navcalc", pk=pk)`` -- yields one
    key per iteration instead of one key reused three times.
    """
    block = _LexWidgets(
        key=key, min_height=min_height, key_parts=(method, model, pk), key_depth=2
    )
    page = block.__enter__()
    result = getattr(page, method)(model, pk, **kwargs)
    block.__exit__(None, None, None)
    return result


def lex_calculation(
    model: str,
    pk: PK,
    *,
    key: Optional[str] = None,
    min_height: int = 48,
    **kwargs: Any,
) -> Optional[dict]:
    """One calculation control -- the Calculate button, its status, its log.

    Takes everything :meth:`WidgetPage.calculation` takes::

        lex_calculation("navcalc", pk=1, variant="action", show_log_button=False)

    Returns the latest status envelope when ``on_status=True``, else ``None``.
    """
    return _solo("calculation", model, pk, key, min_height, kwargs)


def lex_calculation_log(
    model: str,
    pk: PK,
    *,
    key: Optional[str] = None,
    min_height: int = 48,
    **kwargs: Any,
) -> None:
    """The calculation log as a LIVE stream. See :meth:`WidgetPage.calculation_log`."""
    return _solo("calculation_log", model, pk, key, min_height, kwargs)


def lex_calculation_log_tree(
    model: str,
    pk: PK,
    *,
    key: Optional[str] = None,
    min_height: int = 48,
    **kwargs: Any,
) -> None:
    """The log's execution TREE for a finished run.

    See :meth:`WidgetPage.calculation_log_tree`.
    """
    return _solo("calculation_log_tree", model, pk, key, min_height, kwargs)


__all__ = ["lex_widgets", "WidgetPage"]
