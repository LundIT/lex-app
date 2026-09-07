"""Keys that are unique without the author having chosen them.

A Streamlit key has to satisfy two requirements that pull against each other. It
must be **identical on every rerun**, or the component is treated as new and its
state is dropped. It must be **distinct between blocks**, or two blocks share one
``session_state`` slot and read each other's events.

``(file, line)`` of the *caller* satisfies both, and needs nothing from the
author: the same line yields the same key on every rerun because the script runs
top-to-bottom the same way, and two different lines can never collide.

Where a call sits in a loop, ``(file, line)`` is the same for every iteration --
so the flat ``lex_*`` helpers fold what the widget is *about* (model, pk) into
the key as well. That is exactly what distinguishes iterations in practice::

    for pk in (1, 2, 3):
        lex_calculation("navcalc", pk=pk)   # same line, three distinct keys

A ``lex_widgets()`` block in a loop cannot do that -- its contents are declared
after the key is needed -- so two blocks on one line collide. That case raises
Streamlit's own ``DuplicateWidgetID``, which already names the problem and the
fix, so it is deliberately not caught and re-worded here.
"""
from __future__ import annotations

import hashlib
import inspect
import os
import re
from typing import Any, Optional, Tuple

#: Frames inside this package are never the call site we want.
_PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: Long enough that collisions are not a practical concern, short enough that the
#: generated key stays readable in a session-state dump or a DOM inspector.
_DIGEST_LENGTH = 8

_UNSAFE = re.compile(r"[^A-Za-z0-9_]+")


def _sanitise(value: str) -> str:
    """A fragment safe to embed in a key, with runs of junk collapsed."""
    return _UNSAFE.sub("_", value).strip("_")


def caller_site(extra_depth: int = 0) -> Tuple[str, int]:
    """``(filename, lineno)`` of the first frame outside this package.

    Walks ``f_back`` rather than using ``inspect.stack()``, which materialises
    the whole stack with source context for every frame -- far more work than
    two attribute lookups, on a path that runs for every widget on every rerun.
    """
    frame = inspect.currentframe()
    try:
        if frame is not None:
            frame = frame.f_back  # skip caller_site itself
        for _ in range(extra_depth):
            if frame is None:
                break
            frame = frame.f_back
        while frame is not None:
            filename = frame.f_code.co_filename
            if not os.path.abspath(filename).startswith(_PACKAGE_ROOT):
                return filename, frame.f_lineno
            frame = frame.f_back
    finally:
        # Frames hold references to their locals; dropping ours promptly keeps
        # a widget call from pinning the caller's frame for a whole rerun.
        del frame
    return "<unknown>", 0


def widget_key(
    prefix: str,
    explicit: Optional[str] = None,
    *,
    parts: Tuple[Any, ...] = (),
    extra_depth: int = 0,
) -> str:
    """A rerun-stable, block-unique Streamlit key.

    ``explicit`` is kept verbatim inside the result rather than replacing it, so
    a key the author chose stays greppable in a session-state dump while still
    being unique -- which is what makes an author-supplied name useful for
    debugging instead of merely decorative.

    ``parts`` are extra discriminators folded into the digest. The flat helpers
    pass the model and pk so a loop over one line yields one key per iteration.
    """
    filename, lineno = caller_site(extra_depth=extra_depth + 1)
    seed = "\x1f".join([filename, str(lineno), *(str(part) for part in parts)])
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:_DIGEST_LENGTH]

    if explicit:
        return f"{prefix}_{_sanitise(explicit)}_{digest}"
    return f"{prefix}_{digest}"
