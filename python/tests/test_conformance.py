"""Conformance tests over the bundled verdict/fold corpus."""

from __future__ import annotations

import pytest

import nostrhost_protocol as p


def test_conformance_python_corpus():
    result = p.conformance("python")
    assert result["problems"] == [], result["problems"]
    assert len(result["verdicts"]) == 37
    assert len(result["folds"]) == 10


def test_every_verdict_fixture_reaches_expected_verdict(verdicts):
    for fixture in verdicts:
        if "python" not in fixture.get("validators", []):
            continue
        verdict = p.validate_event(fixture["event"])
        expect = fixture["expect"]
        assert bool(verdict.ok) == bool(expect["accept"]), fixture["id"]
        if not expect["accept"]:
            assert verdict.code == expect["code"], fixture["id"]


def test_every_fold_fixture_reaches_expected_fold(folds):
    for fixture in folds:
        if "python" not in fixture.get("validators", []):
            continue
        result = p.fold_events(int(fixture["kind"]), fixture["events"]).as_dict()
        for key, wanted in fixture["expect"].items():
            assert result[key] == wanted, f"{fixture['id']}: {key}"


def test_stable_rejection_code_snapshot():
    """The stable rejection-code vocabulary must not change unexpectedly."""
    codes = sorted(
        {code for spec in p.load_manifest() for code in spec.rejection_codes}
    )
    assert codes == [
        "10000:bad-p",
        "10002:bad-r",
        "27236:bad-expiry",
        "27236:bad-tags",
        "27236:missing-scope",
        "27237:missing-e",
        "30000:bad-p",
        "31100:missing-type",
        "31100:scopes-not-array",
        "31101:missing-schema",
        "31102:admin-not-bool",
        "31102:bad-signer-type",
        "31102:enabled-not-bool",
        "31102:missing-username",
        "content-not-json",
        "d-not-hex64",
        "missing-d",
        "revision-invalid",
        "schema-invalid",
        "subject-mismatch",
    ]


def test_verdict_mismatches_detects_regression():
    # Feed a deliberately wrong code to prove the mismatch checker works.
    fake = [{"id": "x", "accept": True, "code": "", "expect": {"accept": False, "code": "missing-d"}}]
    assert p.conformance.__name__  # sanity
    from nostrhost_protocol.conformance import verdict_mismatches

    assert verdict_mismatches(fake) == ["x: accept=True expected=False"]