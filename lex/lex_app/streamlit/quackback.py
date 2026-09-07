"""The feedback launcher, on the Streamlit page, exactly once.

THE RULE, and it is lex-app's rule rather than a new one: **the top-level
document owns the launcher.** ``index.html`` states it and enforces it with
``window.self !== window.top``, after both failure modes had already happened:

* a Streamlit dashboard with N embedded widgets showed N stacked bubbles, each
  costing its own ``/api/quackback-widget-token`` request;
* and the reverse — a Streamlit page framed by lex-app stacking a second
  launcher over the host's.

This module is the missing third case. A Streamlit page that is NOT framed is a
top-level document with no launcher at all, because lex-app's copy lives in the
React app and this page is not it.

WHY THE FRAME CHECK LOOKS TWO LEVELS UP. A Streamlit custom component is itself
an iframe, so ``window.self !== window.top`` is trivially true here and would
disable the launcher everywhere. The question is not "am I framed" but "is the
STREAMLIT PAGE framed", which is ``host.top !== host`` where ``host`` is
``window.parent``. That is the same reasoning -- and the same code shape -- as
``hide_sidebar_when_framed_js``.

The launcher is injected into the host document rather than rendered here, for
the same reason: anything drawn inside a component iframe is trapped in it, and
a zero-height one at that.
"""
from __future__ import annotations

import os

from lex.streamlit_theme import _js_literal

#: Where the widget SDK and its backing instance live. Same values index.html uses.
QUACKBACK_SDK_URL = "https://hub.excellence-cloud.de/api/widget/sdk.js"
QUACKBACK_INSTANCE_URL = "https://hub.excellence-cloud.de"

#: Marker on the host window, so N reruns do not inject N launchers. Streamlit
#: re-executes the whole script on every interaction; without this the page
#: would accumulate one SDK script per rerun.
_HOST_FLAG = "__lexQuackbackLoaded"


def quackback_enabled() -> bool:
    """Whether to offer the launcher at all.

    Off by an explicit opt-out rather than an opt-in: a deployment that already
    has the widget in lex-app wants it here too, and the one case where it must
    not appear -- being framed -- is decided in the browser where the answer is
    actually knowable.
    """
    raw = os.getenv("LEX_STREAMLIT_QUACKBACK", "").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def _application_key(host_is_local: str) -> str:
    return host_is_local


def quackback_launcher_js(base_url: str) -> str:
    """Script that mounts the feedback launcher on the Streamlit page.

    ``base_url`` is the lex-app origin, because the identify call is a POST to
    lex-app's ``/api/quackback-widget-token`` and the Streamlit page is not
    served from there. A relative URL would resolve against Streamlit and 404.

    A failed identify leaves the launcher up and unidentified rather than
    removing it: someone who wants to send feedback should not be blocked
    because a token call did not come back.
    """
    if not quackback_enabled():
        return ""

    token_url = f"{base_url.rstrip('/')}/api/quackback-widget-token"

    return (
        "<script>\n"
        "  (function () {\n"
        "    var host = window.parent;\n"
        "    if (!host || host === window) return;\n"
        "    // `host.top !== host`, not `window.top !== window`: this script\n"
        "    // always runs inside a component iframe, so asking about ITSELF\n"
        "    // would answer 'framed' everywhere and never show the launcher.\n"
        "    // The question is whether the STREAMLIT PAGE is framed.\n"
        "    var framed;\n"
        "    try { framed = host.top !== host; }\n"
        "    catch (e) { framed = true; }   // cross-origin top: framed by definition\n"
        "    if (framed) {\n"
        "      // lex-app is the top-level document here and owns the launcher.\n"
        "      return;\n"
        "    }\n"
        "    if (host." + _HOST_FLAG + ") return;\n"
        "    host." + _HOST_FLAG + " = true;\n"
        "\n"
        "    var doc = host.document;\n"
        "    var local = host.location.hostname === 'localhost';\n"
        "    var applicationKey = local ? 'lex-app-local' : 'lex-app-production';\n"
        "    var environment = local ? 'local' : 'production';\n"
        "\n"
        "    host.Quackback = host.Quackback || function () {\n"
        "      (host.Quackback.q = host.Quackback.q || []).push(arguments);\n"
        "    };\n"
        "    var s = doc.createElement('script');\n"
        "    s.async = true;\n"
        "    s.crossOrigin = 'anonymous';\n"
        "    s.dataset.applicationKey = applicationKey;\n"
        "    s.dataset.environment = environment;\n"
        "    s.src = " + _js_literal(QUACKBACK_SDK_URL) + ";\n"
        "    doc.head.appendChild(s);\n"
        "\n"
        "    host.Quackback('init', {\n"
        "      instanceUrl: " + _js_literal(QUACKBACK_INSTANCE_URL) + ",\n"
        "      applicationKey: applicationKey,\n"
        "      environment: environment\n"
        "    });\n"
        "\n"
        "    // Cross-origin to lex-app, so credentials must be explicit. If it\n"
        "    // fails the launcher stays up unidentified -- feedback still\n"
        "    // reaches us, it just arrives without a name attached.\n"
        "    host.fetch(" + _js_literal(token_url) + ", {\n"
        "      method: 'POST',\n"
        "      credentials: 'include'\n"
        "    })\n"
        "      .then(function (res) { if (!res.ok) throw new Error('token ' + res.status); return res.json(); })\n"
        "      .then(function (data) {\n"
        "        if (!data || !data.ssoToken) throw new Error('missing ssoToken');\n"
        "        host.Quackback('identify', { ssoToken: data.ssoToken });\n"
        "      })\n"
        "      .catch(function (err) {\n"
        "        console.warn('[lex-quackback] identify failed; the launcher stays "
        "up but anonymous', err);\n"
        "      });\n"
        "  })();\n"
        "</script>\n"
    )
