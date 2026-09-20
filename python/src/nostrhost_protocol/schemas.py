"""JSON Schema loading for the control-plane event protocol.

Schemas ship as package data under ``spec/schemas`` (a mirror of the repo's
``spec/schemas``; a drift test pins them together).
"""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any

_PKG = "nostrhost_protocol"
_SPEC = "spec"


def spec_root() -> Path:
    """Filesystem path to the bundled spec directory (source checkout or wheel)."""
    return Path(str(resources.files(_PKG).joinpath(_SPEC)))


def schemas_dir() -> Path:
    return spec_root() / "schemas"


def fixtures_dir() -> Path:
    return spec_root() / "fixtures"


def load_schema(kind: int) -> dict[str, Any] | None:
    """Load the JSON Schema for *kind* (``<kind>-*.schema.json``), or None."""
    matches = sorted(schemas_dir().glob(f"{kind}-*.schema.json"))
    if not matches:
        return None
    with matches[0].open("rb") as handle:
        return json.load(handle)


def load_all_schemas() -> dict[str, dict[str, Any]]:
    """All bundled schemas keyed by filename."""
    result: dict[str, dict[str, Any]] = {}
    for path in sorted(schemas_dir().glob("*.schema.json")):
        with path.open("rb") as handle:
            result[path.name] = json.load(handle)
    return result


def schema_path_for(kind: int) -> str | None:
    """Relative schema reference (``schemas/<kind>-*.schema.json``) or None."""
    matches = sorted(schemas_dir().glob(f"{kind}-*.schema.json"))
    if not matches:
        return None
    return f"schemas/{matches[0].name}"