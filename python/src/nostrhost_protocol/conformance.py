"""Conformance runner over the bundled verdict/fold corpus."""

from __future__ import annotations

import json
from typing import Any

from .fold import fold
from .schemas import fixtures_dir
from .validate import validate_event


def load_fixtures(name: str) -> list[dict]:
    with (fixtures_dir() / name).open("rb") as handle:
        data = json.load(handle)
    if isinstance(data, dict):
        return data.get("fixtures", [])
    return data


def load_verdicts() -> list[dict]:
    return load_fixtures("verdicts.json")


def load_folds() -> list[dict]:
    return load_fixtures("folds.json")


def run_verdicts(language: str = "python") -> list[dict]:
    results = []
    for fixture in load_verdicts():
        if language not in fixture.get("validators", []):
            continue
        verdict = validate_event(fixture["event"])
        results.append(
            {
                "id": fixture["id"],
                "accept": verdict.ok,
                "code": verdict.code,
                "expect": fixture["expect"],
            }
        )
    return results


def run_folds(language: str = "python") -> list[dict]:
    results = []
    for fixture in load_folds():
        if language not in fixture.get("validators", []):
            continue
        result = fold(int(fixture["kind"]), fixture["events"]).as_dict()
        results.append({"id": fixture["id"], "result": result, "expect": fixture["expect"]})
    return results


def verdict_mismatches(results: list[dict]) -> list[str]:
    problems = []
    for item in results:
        expect = item["expect"]
        if bool(item["accept"]) != bool(expect["accept"]):
            problems.append(
                f"{item['id']}: accept={item['accept']} expected={expect['accept']}"
            )
            continue
        if expect.get("accept") is False and expect.get("code") != item["code"]:
            problems.append(
                f"{item['id']}: code={item['code']} expected={expect.get('code')}"
            )
    return problems


def fold_mismatches(results: list[dict]) -> list[str]:
    problems = []
    for item in results:
        actual, expect = item["result"], item["expect"]
        for key, wanted in expect.items():
            if actual.get(key) != wanted:
                problems.append(
                    f"{item['id']}: {key}={actual.get(key)!r} expected={wanted!r}"
                )
    return problems


def schema_mismatches() -> list[str]:
    """Flag JSON-Schema violations on accepted fixtures (requires jsonschema)."""
    try:
        import jsonschema  # type: ignore
    except ModuleNotFoundError:
        return []
    from .schemas import load_schema, schemas_dir

    problems: list[str] = []
    for fixture in load_verdicts():
        event = fixture["event"]
        kind = int(event["kind"])
        schema = load_schema(kind)
        if schema is None:
            continue
        raw = event.get("content") or ""
        if raw == "":
            continue
        try:
            body = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(body, dict):
            continue
        try:
            jsonschema.Draft7Validator(schema).validate(body)
        except jsonschema.ValidationError as exc:
            if fixture["expect"]["accept"]:
                problems.append(f"{fixture['id']}: schema: {exc.message}")
    return problems


def conformance(language: str = "python") -> dict[str, Any]:
    """Run the full corpus; return verdicts, folds and any problems."""
    verdicts = run_verdicts(language)
    folds = run_folds(language)
    problems = verdict_mismatches(verdicts) + fold_mismatches(folds) + schema_mismatches()
    return {"verdicts": verdicts, "folds": folds, "problems": problems}