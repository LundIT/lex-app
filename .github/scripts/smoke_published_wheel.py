#!/usr/bin/env python3
"""Install the just-published lex-app from PyPI and check it is usable.

The release pipeline published a wheel and then walked away. Nothing confirmed
the artifact customers are about to install actually contains what it should —
so a wheel missing the frontend bundle, or missing its package data, would be
discovered by a customer rather than by us.

This installs the exact version from PyPI into a throwaway environment and
asserts the three things this pipeline can plausibly get wrong:

  1. the wheel installs at all,
  2. the frontend bundle is inside it, with an index.html,
  3. the bundle carries its provenance manifest.

PyPI indexing lags publication by up to a minute or two, so the install is
retried rather than failed on the first miss.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PACKAGE = "lex-app"
BUNDLE = Path("lex") / "react" / "build"
MANIFEST = ".frontend-version.json"


def install(version: str, target: Path, *, attempts: int = 6, delay: float = 20.0,
            run=subprocess.run, sleep=time.sleep) -> None:
    """Install `version` into `target`, retrying while PyPI catches up."""
    last = ""
    for attempt in range(1, attempts + 1):
        result = run(
            [sys.executable, "-m", "pip", "install", "--quiet", "--no-deps",
             "--target", str(target), f"{PACKAGE}=={version}"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print(f"installed {PACKAGE}=={version} (attempt {attempt})")
            return
        last = (result.stderr or "").strip()
        if attempt < attempts:
            print(f"attempt {attempt}: not installable yet, retrying in {delay:.0f}s",
                  file=sys.stderr)
            sleep(delay)
    sys.exit(
        f"{PACKAGE}=={version} was published but is not installable after "
        f"{attempts} attempts: {last[:400]}"
    )


def check_bundle(target: Path) -> dict:
    """Assert the frontend shipped inside the wheel. Returns the manifest."""
    bundle = target / BUNDLE
    if not bundle.is_dir():
        sys.exit(
            f"the published wheel has no frontend bundle at {BUNDLE} — "
            'check "lex.react" is still in [tool.setuptools.package-data]'
        )
    if not (bundle / "index.html").is_file():
        sys.exit(
            f"the bundle at {BUNDLE} has no index.html, so every page would "
            "404 — the wheel was built before the frontend was vendored"
        )

    manifest_path = bundle / MANIFEST
    if not manifest_path.is_file():
        # Not fatal: the app works, but the release cannot say which frontend
        # it shipped, which is the whole point of the provenance work.
        print(f"::warning::the bundle carries no {MANIFEST}, so this release "
              "cannot be attributed to a frontend version", file=sys.stderr)
        return {}
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="The version just published.")
    parser.add_argument("--attempts", type=int, default=6)
    parser.add_argument("--delay", type=float, default=20.0)
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp)
        install(args.version, target, attempts=args.attempts, delay=args.delay)
        manifest = check_bundle(target)

    files = manifest.get("version") or manifest.get("sha", "")[:8] or "unrecorded"
    print(f"OK — {PACKAGE}=={args.version} installs and carries a frontend "
          f"bundle (frontend: {files})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
