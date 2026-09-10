"""Tests for smoke_published_wheel — checking the artifact we just published.

The pipeline used to publish and walk away, so a wheel missing its frontend
bundle would have been found by a customer. These pin the two things worth
getting right: that PyPI's indexing lag is tolerated, and that a missing or
empty bundle fails loudly rather than passing.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "smoke_published_wheel.py"
spec = importlib.util.spec_from_file_location("smoke", SCRIPT)
smoke = importlib.util.module_from_spec(spec)
sys.modules["smoke"] = smoke
spec.loader.exec_module(smoke)


def _run(codes):
    """A `run` returning the given exit codes in order."""
    seq = list(codes)
    calls = []

    def run(argv, **kwargs):
        calls.append(argv)
        class R:
            returncode = seq.pop(0)
            stdout = ""
            stderr = "ERROR: No matching distribution found"
        return R()

    return run, calls


# ── PyPI indexing lag ─────────────────────────────────────────────────

def test_a_version_that_appears_on_the_second_try_is_accepted(tmp_path):
    run, calls = _run([1, 0])
    slept = []
    smoke.install("2.2.1", tmp_path, run=run, sleep=slept.append, delay=0.1)
    assert len(calls) == 2
    assert slept == [0.1], "should have waited once"


def test_a_version_that_never_appears_fails(tmp_path):
    run, calls = _run([1, 1, 1])
    with pytest.raises(SystemExit, match="not installable after 3 attempts"):
        smoke.install("2.2.1", tmp_path, attempts=3, run=run, sleep=lambda _: None)
    assert len(calls) == 3


def test_the_exact_version_is_requested(tmp_path):
    run, calls = _run([0])
    smoke.install("2.2.1", tmp_path, run=run, sleep=lambda _: None)
    assert "lex-app==2.2.1" in calls[0]


# ── What the wheel must contain ───────────────────────────────────────

def _wheel(tmp_path, *, index=True, manifest=None):
    bundle = tmp_path / "lex" / "react" / "build"
    bundle.mkdir(parents=True)
    if index:
        (bundle / "index.html").write_text("<!doctype html>")
    if manifest is not None:
        (bundle / smoke.MANIFEST).write_text(json.dumps(manifest))
    return tmp_path


def test_a_wheel_with_a_bundle_and_a_manifest_passes(tmp_path):
    got = smoke.check_bundle(_wheel(tmp_path, manifest={"version": "1.12.0"}))
    assert got["version"] == "1.12.0"


def test_a_wheel_with_no_bundle_fails(tmp_path):
    # The realistic cause: "lex.react" dropped from package-data.
    with pytest.raises(SystemExit, match="no frontend bundle"):
        smoke.check_bundle(tmp_path)


def test_a_bundle_with_no_index_fails(tmp_path):
    # Every page would 404 with nothing in the logs to explain it.
    with pytest.raises(SystemExit, match="no index.html"):
        smoke.check_bundle(_wheel(tmp_path, index=False))


def test_a_bundle_with_no_manifest_warns_but_passes(tmp_path, capsys):
    # The app works; only the attribution is missing. Not worth failing a
    # release that is already published.
    got = smoke.check_bundle(_wheel(tmp_path))
    assert got == {}
    assert "cannot be attributed" in capsys.readouterr().err
