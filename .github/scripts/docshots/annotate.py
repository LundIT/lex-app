#!/usr/bin/env python3
"""Turn a `Shot` plus captions into an annotated, animated SVG.

One renderer for both capture front-ends. A terminal shot draws its own text;
a browser shot embeds a PNG; from there the callout geometry is identical, so
a CLI walkthrough and a UI walkthrough look like the same document.

Output is a single self-contained `.svg` file, meant to be referenced from
markdown the ordinary way:

    ![Running the test groups](../images/cli/pytest-groups.svg)

That matters for the docs site: Quartz strips raw HTML from markdown, but an
`<img>` pointing at an SVG file renders, and CSS animation inside that file
still runs — so the arrows draw themselves without the site needing to know
anything about it.

Colour does NOT come from the reader's theme. `prefers-color-scheme` inside an
`<img>`-loaded SVG is not reliably delivered (measured: Chromium renders both
schemes identically, even with the SVG loaded as the document), so each figure
declares the surface that matches what it is showing and the page behind it
stays transparent.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path

from docshots.model import Box, Shot

GUTTER = 300.0        # width of the caption column
GUTTER_GAP = 34.0     # space between the picture and the captions
LABEL_PAD = 11.0
LABEL_LH = 17.0
LABEL_CHARS = 34      # wrap width, in characters
LABEL_CW = 6.9        # caption advance width, for box sizing only
STEP_DELAY = 0.55     # seconds between one callout appearing and the next


@dataclass
class Callout:
    """A caption pointing at a named anchor.

    `step` renders a numbered badge; leave it None for an unnumbered note.
    Numbering is the reader's promise that order matters, so it is opt-in
    rather than automatic — a page pointing out three independent things on
    one screen should not imply a sequence.
    """

    anchor: str
    text: str
    step: int | None = None


def _wrap(text: str, width: int = LABEL_CHARS) -> list[str]:
    out, line = [], ""
    for word in text.split():
        candidate = f"{line} {word}".strip()
        if len(candidate) > width and line:
            out.append(line)
            line = word
        else:
            line = candidate
    if line:
        out.append(line)
    return out or [""]


SURFACES = {
    # Each surface is a complete, self-sufficient palette. There is no media
    # query here on purpose: an SVG loaded through `<img>` does not reliably
    # receive the reader's colour-scheme preference — measured in Chromium,
    # both schemes render identically, even with the SVG as the document — so
    # a picture that relied on one would be a coin flip. The surface is chosen
    # to match the thing being annotated instead: dark for a terminal, light
    # for a screenshot of the app in its light theme.
    "dark": {
        "panel": "#20262e", "ink": "#e6ebf2", "line": "#39434f",
        "term_bg": "#20262e", "term_ink": "#dfe5ee",
        "accent": "#3fb8c9", "accent_soft": "rgba(63,184,201,.16)",
    },
    "light": {
        "panel": "#ffffff", "ink": "#1c2430", "line": "#d7dce4",
        "term_bg": "#20262e", "term_ink": "#dfe5ee",
        "accent": "#0f7d8c", "accent_soft": "rgba(15,125,140,.14)",
    },
}


def _theme_css(surface: str) -> str:
    """One palette, written out flat.

    The page itself stays transparent so the figure sits on whatever the docs
    page paints rather than punching a slab of the wrong colour into it.
    """
    try:
        s = SURFACES[surface]
    except KeyError:
        raise ValueError(f"unknown surface {surface!r}; expected one of {sorted(SURFACES)}")
    return (
        "  :root{"
        + "".join(f"--ds-{k.replace('_', '-')}:{v};" for k, v in s.items())
        + "}\n"
    )


def _static_css() -> str:
    """Final state, no motion.

    Not every place a docs picture lands can animate: a PDF export, a release
    email, GitHub's own markdown renderer. The static build is the same
    drawing with every callout already shown, so one source produces both and
    the animated one is never the only readable version.
    """
    return (
        "  .ds-arrow{stroke-dashoffset:0}\n"
        "  .ds-label,.ds-badge{opacity:1}\n"
        "  .ds-halo{opacity:.85}\n"
    )


def _anim_css(count: int) -> str:
    """Draw-on animation, staggered per callout, and disabled when asked.

    `prefers-reduced-motion` collapses every delay to zero rather than
    removing the final state: the picture must be complete and readable for a
    reader who never sees a frame of the animation.
    """
    rules = [
        "  @keyframes ds-draw{to{stroke-dashoffset:0}}",
        "  @keyframes ds-fade{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}",
        "  @keyframes ds-ring{0%,100%{opacity:.55}50%{opacity:1}}",
        "  .ds-arrow{stroke-dasharray:var(--len);stroke-dashoffset:var(--len);"
        "animation:ds-draw .5s ease-out forwards}",
        "  .ds-label,.ds-badge{opacity:0;animation:ds-fade .4s ease-out forwards}",
        "  .ds-halo{animation:ds-ring 2.4s ease-in-out infinite}",
    ]
    for i in range(count):
        d = i * STEP_DELAY
        rules.append(
            f"  .ds-s{i} .ds-arrow{{animation-delay:{d + .18:.2f}s}}"
            f"  .ds-s{i} .ds-label,.ds-s{i} .ds-badge{{animation-delay:{d:.2f}s}}"
            f"  .ds-s{i} .ds-halo{{animation-delay:{d:.2f}s}}"
        )
    rules.append(
        "  @media (prefers-reduced-motion: reduce){"
        ".ds-arrow{stroke-dashoffset:0;animation:none}"
        ".ds-label,.ds-badge{opacity:1;animation:none}"
        ".ds-halo{animation:none;opacity:.8}}"
    )
    return "\n".join(rules)


def _terminal_body(shot: Shot) -> str:
    """The terminal grid, one glyph per x position so columns cannot drift."""
    c = shot.cells or {}
    cw, ch = c.get("cell_w", 8.4), c.get("cell_h", 18.0)
    px, py, chrome = c.get("pad_x", 16.0), c.get("pad_y", 14.0), c.get("chrome_h", 32.0)
    parts = [
        f'<rect x="0" y="0" width="{shot.width:.1f}" height="{shot.height:.1f}" '
        f'rx="10" fill="var(--ds-term-bg)"/>',
        f'<rect x="0" y="0" width="{shot.width:.1f}" height="{chrome:.1f}" '
        f'rx="10" fill="var(--ds-term-bg)"/>',
        f'<rect x="0" y="{chrome - 10:.1f}" width="{shot.width:.1f}" height="10" '
        f'fill="var(--ds-term-bg)"/>',
        f'<line x1="0" y1="{chrome:.1f}" x2="{shot.width:.1f}" y2="{chrome:.1f}" '
        f'stroke="rgba(255,255,255,.09)"/>',
    ]
    for i, colour in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        parts.append(f'<circle cx="{18 + i * 17}" cy="{chrome / 2:.1f}" r="5.5" fill="{colour}"/>')
    if shot.title:
        parts.append(
            f'<text x="{shot.width / 2:.1f}" y="{chrome / 2 + 4:.1f}" text-anchor="middle" '
            f'font-size="11.5" fill="rgba(223,229,238,.55)" '
            f'font-family="ui-monospace,SFMono-Regular,Menlo,monospace">'
            f"{escape(shot.title)}</text>"
        )

    def row_y(r: int) -> float:
        return chrome + py + r * ch + ch * 0.72

    def glyph_run(text: str, col: int, y: float, fill: str, weight: str, opacity: str) -> str:
        xs = " ".join(f"{px + (col + i) * cw:.1f}" for i in range(len(text)))
        return (
            f'<text x="{xs}" y="{y:.1f}" fill="{fill}" font-weight="{weight}"{opacity} '
            f'font-size="13" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" '
            f'xml:space="preserve">{escape(text)}</text>'
        )

    r0 = 0
    if c.get("command"):
        y = row_y(0)
        parts.append(glyph_run("$", 0, y, "var(--ds-accent)", "700", ""))
        parts.append(glyph_run(c["command"], 2, y, "var(--ds-term-ink)", "600", ""))
        r0 = 1

    for r, runs in enumerate(c.get("lines", [])):
        y, col = row_y(r + r0), 0
        for run in runs:
            t = run["text"]
            if t.strip():
                parts.append(glyph_run(
                    t, col, y,
                    run.get("fg") or "var(--ds-term-ink)",
                    "700" if run.get("bold") else "400",
                    ' opacity="0.62"' if run.get("dim") else "",
                ))
            col += len(t)
    return "\n".join(parts)


def _image_body(shot: Shot) -> str:
    return (
        f'<rect x="0" y="0" width="{shot.width:.1f}" height="{shot.height:.1f}" rx="10" '
        f'fill="var(--ds-panel)"/>'
        f'<image x="0" y="0" width="{shot.width:.1f}" height="{shot.height:.1f}" '
        f'href="{shot.image_href}" preserveAspectRatio="xMidYMid meet"/>'
        f'<rect x="0.5" y="0.5" width="{shot.width - 1:.1f}" height="{shot.height - 1:.1f}" '
        f'rx="10" fill="none" stroke="var(--ds-line)"/>'
    )


def _place_labels(items: list[tuple[Callout, Box]], height: float) -> list[float]:
    """Caption tops, in anchor order, pushed apart just enough not to overlap."""
    tops, cursor = [], 0.0
    for callout, box in items:
        h = len(_wrap(callout.text)) * LABEL_LH + LABEL_PAD * 2
        top = max(box.cy - h / 2, cursor)
        tops.append(top)
        cursor = top + h + 14
    overflow = (tops[-1] + len(_wrap(items[-1][0].text)) * LABEL_LH + LABEL_PAD * 2) - height if tops else 0
    if overflow > 0:  # ran off the bottom — slide the whole stack up
        tops = [max(0.0, t - overflow) for t in tops]
    return tops


def render(shot: Shot, callouts: list[Callout], *, strict: bool = True,
           animate: bool = True, surface: str = "dark") -> str:
    """The annotated SVG.

    `strict` raises when a callout names an anchor the capture could not
    resolve. That is the whole point of anchoring to selectors and regexes:
    when the product moves, the build says so instead of shipping a picture
    with an arrow pointing at nothing.
    """
    def clamp(b: Box) -> Box:
        """Keep a box inside the picture.

        A DOM element can legitimately be wider than the screenshot that
        contains it — an AG Grid row is as wide as all its columns, including
        the ones scrolled out of view — and an unclamped highlight then runs
        off the canvas and through the captions. Clamping keeps the highlight
        on the part the reader can actually see, which is the part being
        talked about.
        """
        x = min(max(b.x, 0.0), shot.width)
        y = min(max(b.y, 0.0), shot.height)
        return Box(x=x, y=y,
                   width=max(min(b.x + b.width, shot.width) - x, 1.0),
                   height=max(min(b.y + b.height, shot.height) - y, 1.0))

    resolved: list[tuple[Callout, Box]] = []
    problems: list[str] = []
    for c in callouts:
        a = shot.anchor(c.anchor)
        if a is None:
            problems.append(f"{c.anchor!r}: no such anchor in the shot")
        elif not a.found or a.box is None:
            problems.append(f"{c.anchor!r}: {a.detail or 'not found in the capture'}")
        else:
            resolved.append((c, clamp(a.box)))
    if problems and strict:
        raise ValueError("annotation anchors did not resolve:\n  " + "\n  ".join(problems))

    resolved.sort(key=lambda cb: (cb[1].y, cb[1].x))
    tops = _place_labels(resolved, shot.height)

    total_w = shot.width + GUTTER_GAP + GUTTER
    total_h = max(shot.height, (tops[-1] + 90) if tops else 0) + 8

    body = _terminal_body(shot) if shot.cells else _image_body(shot)
    layers: list[str] = []

    for i, ((callout, box), top) in enumerate(zip(resolved, tops)):
        lines = _wrap(callout.text)
        lw = min(GUTTER, max(len(l) for l in lines) * LABEL_CW + LABEL_PAD * 2 +
                 (26 if callout.step is not None else 0))
        lh = len(lines) * LABEL_LH + LABEL_PAD * 2
        lx = shot.width + GUTTER_GAP

        # Arrow: from the caption's left edge to the nearest edge of the target.
        x2 = min(box.x + box.width + 6, shot.width - 2)
        y2 = box.cy
        x1, y1 = lx - 8, top + lh / 2
        cx = (x1 + x2) / 2
        path = f"M{x1:.1f},{y1:.1f} C{cx:.1f},{y1:.1f} {cx:.1f},{y2:.1f} {x2 + 10:.1f},{y2:.1f}"
        length = abs(x1 - x2) + abs(y1 - y2) + 40

        halo = (
            f'<rect class="ds-halo" x="{box.x - 4:.1f}" y="{box.y - 3:.1f}" '
            f'width="{box.width + 8:.1f}" height="{box.height + 6:.1f}" rx="5" '
            f'fill="var(--ds-accent-soft)" stroke="var(--ds-accent)" stroke-width="1.6"/>'
        )
        arrow = (
            f'<path class="ds-arrow" d="{path}" fill="none" stroke="var(--ds-accent)" '
            f'stroke-width="2" stroke-linecap="round" marker-end="url(#ds-head)" '
            f'style="--len:{length:.0f}"/>'
        )

        tx = lx + LABEL_PAD + (26 if callout.step is not None else 0)
        tspans = "".join(
            f'<tspan x="{tx:.1f}" dy="{0 if j == 0 else LABEL_LH}">{escape(l)}</tspan>'
            for j, l in enumerate(lines)
        )
        badge = ""
        if callout.step is not None:
            badge = (
                f'<g class="ds-badge">'
                f'<circle cx="{lx + LABEL_PAD + 9:.1f}" cy="{top + LABEL_PAD + 8:.1f}" r="10" '
                f'fill="var(--ds-accent)"/>'
                f'<text x="{lx + LABEL_PAD + 9:.1f}" y="{top + LABEL_PAD + 12:.1f}" '
                f'text-anchor="middle" font-size="11.5" font-weight="700" fill="#fff" '
                f'font-family="system-ui,-apple-system,Segoe UI,sans-serif">{callout.step}</text>'
                f"</g>"
            )
        label = (
            f'<g class="ds-label">'
            f'<rect x="{lx:.1f}" y="{top:.1f}" width="{lw:.1f}" height="{lh:.1f}" rx="8" '
            f'fill="var(--ds-panel)" stroke="var(--ds-line)"/>'
            f'<text y="{top + LABEL_PAD + 12:.1f}" font-size="13" fill="var(--ds-ink)" '
            f'font-family="system-ui,-apple-system,Segoe UI,Roboto,sans-serif">{tspans}</text>'
            f"</g>"
        )
        # Badge after the label: the label's own rect is opaque, so a badge
        # drawn before it is simply painted over.
        layers.append(f'<g class="ds-s{i}">{halo}{arrow}{label}{badge}</g>')

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_w:.0f}" height="{total_h:.0f}" \
viewBox="0 0 {total_w:.0f} {total_h:.0f}" role="img" \
aria-label="{escape(shot.title or 'annotated screenshot')}">
<style>
{_theme_css(surface)}{_anim_css(len(resolved)) if animate else _static_css()}
</style>
<defs>
  <marker id="ds-head" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">
    <path d="M0,0 L10,5 L0,10 z" fill="var(--ds-accent)"/>
  </marker>
</defs>
<g>{body}</g>
{"".join(layers)}
</svg>
"""


def write(shot: Shot, callouts: list[Callout], path: str | Path, *,
          strict: bool = True, animate: bool = True, surface: str = "dark") -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(render(shot, callouts, strict=strict, animate=animate, surface=surface),
                 encoding="utf-8")
    return p
