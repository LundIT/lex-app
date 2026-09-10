#!/usr/bin/env python3
"""Install the published frontend and vendor it into lex/react/build/.

Run at release time, before the lex-app wheel is built. lex-app is a pip
package, so the frontend travels the same way: it is published to PyPI as
`lex-app-frontend`, installed here, and its files copied into the tree so they ship
inside the lex-app wheel exactly as they do today.

Which version is used comes from `frontend-version.txt`:

    latest      take whatever is newest on PyPI  (the default)
    1.10.0      take exactly that

`latest` is convenient and NOT reproducible: six months later, nothing in the
git tag says which frontend that release shipped. So the resolved version is
always written into the bundle as `.frontend-version.json`, which ships inside
the wheel — and the release workflow records it on the GitHub release too.
Pin the file when you need a release you can rebuild.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1].parent
SPEC_PATH = REPO_ROOT / "frontend-version.txt"
BUNDLE_PATH = REPO_ROOT / "lex" / "react" / "build"
MANIFEST_NAME = ".frontend-version.json"
PACKAGE = "lex-app-frontend"


def read_spec(path: Path = SPEC_PATH) -> str:
    """The requested version: an exact version, or 'latest'.

    A missing file means 'latest'. That keeps the default behaviour the one
    the team asked for, without requiring the file to exist everywhere.
    """
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if line:
                return line
    except OSError:
        pass
    return "latest"


def pip_spec(requested: str) -> str:
    """The argument to hand pip."""
    return PACKAGE if requested == "latest" else f"{PACKAGE}=={requested}"


def installed_version(target: Path, *, run=subprocess.run) -> str:
    """The version pip actually installed, read from the dist-info directory.

    Read back rather than assumed: with `latest` we do not know it in advance,
    and it is the one fact this whole step exists to establish.
    """
    matches = sorted(target.glob("lex_app_frontend-*.dist-info"))
    if not matches:
        sys.exit(
            f"{PACKAGE} was not installed into {target} — pip reported success "
            "but left no dist-info, so the version cannot be established"
        )
    # lex_app_frontend-1.10.0.dist-info -> 1.10.0
    return matches[-1].name[len("lex_app_frontend-"):-len(".dist-info")]


def installed_commit(target: Path) -> str | None:
    """The frontend commit the installed package records, or None.

    Read out of the package's own source rather than imported, because the
    package is installed into a throwaway directory that is not on sys.path
    and importing it would pull a second copy of the module into this process.

    None is tolerated: the manifest is still written, just without a sha, and
    the release notes then report a gap rather than a wrong range.
    """
    init = target / "lex_app_frontend" / "__init__.py"
    try:
        text = init.read_text(encoding="utf-8")
    except OSError:
        return None
    match = re.search(r'^_COMMIT = "([0-9a-f]{40})"$', text, re.M)
    return match.group(1) if match else None


def resolve(requested: str, *, run=subprocess.run) -> str:
    """The concrete version `requested` names, without touching the tree.

    `latest` is convenient but it resolves to whatever is newest at the moment
    it runs. Resolving once at the gate — and recording it on the prerelease —
    turns that into a decision somebody can see before promoting, instead of a
    lottery run again at publish time.
    """
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp)
        result = run(
            [sys.executable, "-m", "pip", "install", "--quiet", "--no-deps",
             "--target", str(target), pip_spec(requested)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            sys.exit(
                f"could not resolve {pip_spec(requested)}: "
                f"{(result.stderr or '').strip() or f'pip exited {result.returncode}'}"
            )
        return installed_version(target)


def vendor(requested: str, *, run=subprocess.run, bundle_path: Path = BUNDLE_PATH) -> str:
    """Install `requested` and copy its bundle into the tree. Returns the version."""
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp)
        result = run(
            [sys.executable, "-m", "pip", "install", "--quiet", "--no-deps",
             "--target", str(target), pip_spec(requested)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            sys.exit(
                f"could not install {pip_spec(requested)}: "
                f"{(result.stderr or '').strip() or f'pip exited {result.returncode}'}"
            )

        version = installed_version(target)
        commit = installed_commit(target)
        source = target / "lex_app_frontend" / "build"
        if not source.is_dir() or not (source / "index.html").is_file():
            sys.exit(
                f"{PACKAGE} {version} contains no usable bundle at {source} — "
                "the published wheel was built without a frontend build"
            )

        # Replaced, not merged: asset filenames are content hashes, so merging
        # would leave a previous frontend's assets beside the new one and the
        # shipped bundle would depend on what was in the tree beforehand.
        if bundle_path.exists():
            shutil.rmtree(bundle_path)
        bundle_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, bundle_path)

    # `sha` first and unconditionally named: release_notes.manifest.validate
    # and ranges.frontend_sha_at both require a 40-character sha and ignore
    # everything else. Writing only `version` here would leave the range
    # unresolvable through either path — a pin needs BOTH tags to carry one,
    # and the manifest fallback needs a sha. That gap is what this release
    # pipeline exists to close, so the two writers have to agree.
    manifest = {
        "package": PACKAGE,
        "version": version,
        "requested": requested,
        "vendored_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if commit:
        manifest["sha"] = commit
        manifest["repo"] = "ExcellenceCloudGmbH/process-admin-general-client"
    else:
        print(
            f"{PACKAGE} {version} records no build commit, so the manifest "
            "carries no sha and the release note will report a frontend gap. "
            "Publish it from a version of the frontend that stamps _COMMIT.",
            file=sys.stderr,
        )
    (bundle_path / MANIFEST_NAME).write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    files = sum(1 for p in bundle_path.rglob("*") if p.is_file())
    print(f"vendored {PACKAGE} {version} (requested: {requested}, "
          f"commit: {commit[:8] if commit else 'unknown'}): "
          f"{files} files into {bundle_path}")
    return version


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--version",
        help="Override frontend-version.txt. 'latest' or an exact version.",
    )
    parser.add_argument(
        "--print-version", action="store_true",
        help="Print only the resolved version, for a workflow to capture.",
    )
    parser.add_argument(
        "--resolve-only", action="store_true",
        help="Print the version `latest` resolves to and change nothing.",
    )
    args = parser.parse_args(argv)

    requested = args.version or read_spec()

    if args.resolve_only:
        print(resolve(requested))
        return 0

    version = vendor(requested)
    if args.print_version:
        print(version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
