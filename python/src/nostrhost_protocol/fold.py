"""Deterministic addressable-state folding (``spec/envelope.md`` §3)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .validate import _content_key, _parse_content, _tag, declares_revision, revision_of, validate_event


@dataclass
class FoldResult:
    subject: str = ""
    revision: int = 0
    enabled: bool = True
    conflicts: int = 0
    fact: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "subject": self.subject,
            "revision": self.revision,
            "enabled": self.enabled,
            "conflicts": self.conflicts,
            "fact": self.fact,
        }


def fold(kind: int, events: list[dict]) -> FoldResult:
    valid = [event for event in events if validate_event(event).ok]
    if not valid:
        return FoldResult()
    ordered = sorted(
        valid,
        key=lambda e: (revision_of(e), int(e.get("created_at", 0)), str(e.get("id", ""))),
    )
    winner = ordered[-1]
    top_revision = revision_of(winner)
    winner_key = _content_key(winner)
    # A conflict is two events that *explicitly* declare the same revision but
    # would fold to different facts; such a tie is broken by (created_at, id).
    # Legacy documents that omit `revision` are ordinary NIP-33 replacement —
    # time ordering, not a conflict — and exact duplicates are idempotent
    # (envelope.md §3 step 4).
    conflicts = sum(
        1
        for e in valid
        if declares_revision(e)
        and revision_of(e) == top_revision
        and _content_key(e) != winner_key
    )
    body, _ = _parse_content(winner)
    body = body if isinstance(body, dict) else {}
    d = _tag(winner, "d")
    subject = d[1] if d and len(d) >= 2 else body.get("subject", "")
    enabled = body.get("enabled", True)
    if not isinstance(enabled, bool):
        enabled = True
    fact: dict
    if kind == 31100:
        fact = {"type": body.get("type", ""), "scopes": list(body.get("scopes", []))}
    elif kind == 31102:
        fact = {"username": body.get("username", ""), "signer_type": body.get("signer_type", "")}
    elif kind == 31101:
        fact = {"schema": body.get("schema"), "value": body.get("value", {})}
    else:
        fact = {}
    return FoldResult(
        subject=subject,
        revision=top_revision,
        enabled=enabled,
        conflicts=max(0, conflicts),
        fact=fact,
    )


fold_events = fold