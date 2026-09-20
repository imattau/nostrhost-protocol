"""Drift guards: bundled spec data must match the repo's authoritative spec/.

These tests only run when the package is imported from a source checkout of the
nostrhost-protocol repository (the repo root is a sibling of ``python/``); a
standalone install has no repo copy to compare against and skips.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from nostrhost_protocol import schemas


def _repo_root() -> Path | None:
    candidate = Path(__file__).resolve().parents[2]  # python/tests -> python -> repo
    if (candidate / "spec").is_dir():
        return candidate
    return None


@pytest.fixture(scope="module")
def repo_root() -> Path | None:
    return _repo_root()


def _walk(path: Path) -> dict[str, bytes]:
    return {str(p.relative_to(path)): p.read_bytes() for p in sorted(path.rglob("*")) if p.is_file()}


def test_bundled_fixtures_match_repo(repo_root):
    if repo_root is None:
        pytest.skip("not a source checkout")
    repo = _walk(repo_root / "spec" / "fixtures")
    bundled = _walk(schemas.fixtures_dir())
    assert bundled == repo, f"fixture drift: {set(bundled) ^ set(repo)}"


def test_bundled_schemas_match_repo(repo_root):
    if repo_root is None:
        pytest.skip("not a source checkout")
    repo = _walk(repo_root / "spec" / "schemas")
    bundled = _walk(schemas.schemas_dir())
    assert bundled == repo, f"schema drift: {set(bundled) ^ set(repo)}"


def test_bundled_manifest_and_envelope_match_repo(repo_root):
    if repo_root is None:
        pytest.skip("not a source checkout")
    for name in ("manifest.json", "envelope.md"):
        repo = (repo_root / "spec" / name).read_bytes()
        bundled = (schemas.spec_root() / name).read_bytes()
        assert bundled == repo, f"{name} drift"