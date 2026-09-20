"""Shared pytest fixtures for the nostrhost-protocol package."""

from __future__ import annotations

import json

import pytest

from nostrhost_protocol.schemas import fixtures_dir


@pytest.fixture(scope="session")
def verdicts() -> list[dict]:
    with (fixtures_dir() / "verdicts.json").open("rb") as handle:
        data = json.load(handle)
    return data["fixtures"]


@pytest.fixture(scope="session")
def folds() -> list[dict]:
    with (fixtures_dir() / "folds.json").open("rb") as handle:
        data = json.load(handle)
    return data["fixtures"]