"""Manifest/schema-loading and standalone-wheel tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

import nostrhost_protocol as p


def test_load_all_schemas_returns_bundled_set():
    schemas = p.load_all_schemas()
    assert set(schemas) == {
        "10000-mute-list.schema.json",
        "10002-relay-list.schema.json",
        "27236-delegation.schema.json",
        "27237-revocation.schema.json",
        "30000-permission-set.schema.json",
        "30078-app-data.schema.json",
        "31100-capability.schema.json",
        "31101-policy.schema.json",
        "31102-identity.schema.json",
        "envelope.schema.json",
    }


def test_load_schema_and_reference():
    assert p.load_schema(31100) is not None
    assert p.schema_path_for(31100) == "schemas/31100-capability.schema.json"
    assert p.load_schema(99999) is None
    assert p.schema_path_for(99999) is None


def test_manifest_find_and_codes():
    spec = p.find_kind(31100)
    assert spec is not None
    assert spec.name == "capability"
    assert spec.category == "addressable-document"
    assert "31100:missing-type" in spec.rejection_codes
    assert p.rejection_codes_for(10000) == ["10000:bad-p"]


def test_manifest_json_is_valid():
    raw = json.loads(Path(p.manifest_path()).read_text())
    assert raw["schema"] == 1
    assert raw["protocol"] == "nostrhost-control-plane-events"


def test_validate_manifest_reports_duplicate():
    assert p.duplicate_kinds() == []


@pytest.mark.skipif(sys.platform == "win32", reason="uses uv build")
def test_standalone_wheel_build_and_install(tmp_path):
    """Build the wheel with uv and verify it imports + runs conformance standalone."""
    root = Path(__file__).resolve().parents[2]
    wheel_dir = root / "python" / "dist"
    wheel_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(wheel_dir)],
        cwd=root / "python",
        check=True,
        capture_output=True,
    )
    wheels = list(wheel_dir.glob("nostrhost_protocol-*.whl"))
    assert wheels, "no wheel produced"
    target = tmp_path / "venv"
    subprocess.run(
        [sys.executable, "-m", "venv", str(target)],
        check=True,
        capture_output=True,
    )
    pip = target / "bin" / "pip"
    subprocess.run([str(pip), "install", "-q", str(wheels[0])], check=True, capture_output=True)
    python = target / "bin" / "python"
    out = subprocess.run(
        [str(python), "-c",
         "from nostrhost_protocol import conformance;"
         "r=conformance();assert not r['problems'], r['problems'];"
         "print(len(r['verdicts']), len(r['folds']))"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert out.stdout.strip() == "37 10", out.stdout