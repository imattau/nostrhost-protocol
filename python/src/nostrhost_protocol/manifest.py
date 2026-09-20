"""Machine-readable kind manifest access.

The manifest (``spec/manifest.json``) is the authority for event names, kinds,
categories, schema versions, schema references and stable rejection codes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .schemas import spec_root


@dataclass
class KindSpec:
    kind: int
    name: str
    category: str
    addressable: bool = False
    retention: str = "immutable"
    nip: str | None = None
    schema_version: int | None = None
    schema: str | None = None
    rejection_codes: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "KindSpec":
        return cls(
            kind=int(raw["kind"]),
            name=raw["name"],
            category=raw["category"],
            addressable=bool(raw.get("addressable", False)),
            retention=raw.get("retention", "immutable"),
            nip=raw.get("nip"),
            schema_version=raw.get("schema_version"),
            schema=raw.get("schema"),
            rejection_codes=list(raw.get("rejection_codes", [])),
        )


def manifest_path() -> str:
    return str(spec_root() / "manifest.json")


def load_manifest() -> list[KindSpec]:
    with open(manifest_path(), "rb") as handle:
        data = json.load(handle)
    return [KindSpec.from_dict(raw) for raw in data.get("kinds", [])]


def iter_kinds() -> list[KindSpec]:
    return load_manifest()


def find_kind(kind: int) -> KindSpec | None:
    for spec in load_manifest():
        if spec.kind == kind:
            return spec
    return None


def rejection_codes_for(kind: int) -> list[str]:
    spec = find_kind(kind)
    return list(spec.rejection_codes) if spec else []


def schema_reference_for(kind: int) -> str | None:
    spec = find_kind(kind)
    return spec.schema if spec else None


def duplicate_kinds() -> list[int]:
    """Kinds that appear more than once in the manifest (should be empty)."""
    seen: dict[int, int] = {}
    for spec in load_manifest():
        seen[spec.kind] = seen.get(spec.kind, 0) + 1
    return [kind for kind, count in seen.items() if count > 1]


def validate_manifest() -> list[str]:
    """Structural consistency problems in the manifest (should be empty)."""
    problems: list[str] = []
    for spec in load_manifest():
        if not spec.name:
            problems.append(f"kind {spec.kind}: missing name")
        if spec.schema is not None:
            reference = spec.schema.removeprefix("schemas/")
            if not (spec_root() / "schemas" / reference).exists():
                problems.append(f"kind {spec.kind}: schema {spec.schema!r} not found")
        if spec.rejection_codes:
            for code in spec.rejection_codes:
                if not code:
                    problems.append(f"kind {spec.kind}: empty rejection code")
    for kind in duplicate_kinds():
        problems.append(f"duplicate kind {kind}")
    return problems