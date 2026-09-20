"""Event validation implementing ``spec/envelope.md`` exactly.

Port of the reference implementation (formerly ``tools/event_protocol.py``).
Rules are applied in the documented order; the first failing rule wins and its
stable code is returned.
"""

from __future__ import annotations

import json
import re
from typing import Any

from .kinds import ADDRESSABLE_KINDS, HEX64_D_KINDS, JSON_CONTENT_KINDS, SIGNER_TYPES
from .verdict import Verdict

_HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
_WS_URL = re.compile(r"^wss?://", re.IGNORECASE)


def is_hex64(value: str) -> bool:
    return bool(_HEX64.match(value))


def _tag(event: dict, name: str) -> list[str] | None:
    for tag in event.get("tags", []):
        if tag and tag[0] == name:
            return tag
    return None


def _tags(event: dict, name: str) -> list[list[str]]:
    return [tag for tag in event.get("tags", []) if tag and tag[0] == name]


def _parse_content(event: dict) -> tuple[object, bool]:
    """Return (parsed, ok). Empty content parses to {} with ok True."""
    raw = event.get("content") or ""
    if raw == "":
        return {}, True
    try:
        return json.loads(raw), True
    except (ValueError, TypeError):
        return None, False


def validate_event(event: dict) -> Verdict:
    """Apply the event-protocol rules in order; return the first failure."""
    kind = int(event.get("kind", 0))
    content, content_ok = _parse_content(event)

    if kind in JSON_CONTENT_KINDS and not content_ok:
        return Verdict(False, "content-not-json")
    body = content if isinstance(content, dict) else {}

    d = _tag(event, "d")
    if kind in ADDRESSABLE_KINDS:
        if d is None or len(d) < 2 or d[1] == "":
            return Verdict(False, "missing-d")
        if kind in HEX64_D_KINDS and not is_hex64(d[1]):
            return Verdict(False, "d-not-hex64")

    if "schema" in body:
        schema = body["schema"]
        if not isinstance(schema, int) or isinstance(schema, bool) or schema < 1:
            return Verdict(False, "schema-invalid")
    if "revision" in body:
        revision = body["revision"]
        if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
            return Verdict(False, "revision-invalid")
    if "subject" in body and d is not None and len(d) >= 2 and body["subject"] != d[1]:
        return Verdict(False, "subject-mismatch")

    if kind == 31100:
        if not isinstance(body.get("type"), str) or not body["type"]:
            return Verdict(False, "31100:missing-type")
        scopes = body.get("scopes")
        if scopes is not None and (
            not isinstance(scopes, list) or any(not isinstance(s, str) for s in scopes)
        ):
            return Verdict(False, "31100:scopes-not-array")
    elif kind == 31101:
        if "schema" not in body:
            return Verdict(False, "31101:missing-schema")
    elif kind == 31102:
        enabled = body.get("enabled", True)
        if not isinstance(enabled, bool):
            return Verdict(False, "31102:enabled-not-bool")
        if "admin" in body and not isinstance(body["admin"], bool):
            return Verdict(False, "31102:admin-not-bool")
        username = body.get("username")
        if enabled and (not isinstance(username, str) or not username.strip()):
            return Verdict(False, "31102:missing-username")
        signer_type = body.get("signer_type")
        if signer_type not in (None, "") and signer_type not in SIGNER_TYPES:
            return Verdict(False, "31102:bad-signer-type")
    elif kind == 27236:
        p = _tag(event, "p")
        server = _tag(event, "server")
        if (
            p is None
            or len(p) < 2
            or not is_hex64(p[1])
            or server is None
            or len(server) < 2
            or not is_hex64(server[1])
        ):
            return Verdict(False, "27236:bad-tags")
        expiry = _tag(event, "expiry")
        if expiry is None or len(expiry) < 2:
            return Verdict(False, "27236:bad-expiry")
        try:
            if int(expiry[1]) <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return Verdict(False, "27236:bad-expiry")
        if not _tags(event, "scope"):
            return Verdict(False, "27236:missing-scope")
    elif kind == 27237:
        e = _tag(event, "e")
        if e is None or len(e) < 2 or not is_hex64(e[1]):
            return Verdict(False, "27237:missing-e")
    elif kind == 30000:
        for tag in _tags(event, "p"):
            if len(tag) < 2 or not is_hex64(tag[1]):
                return Verdict(False, "30000:bad-p")
    elif kind == 10000:
        for tag in _tags(event, "p"):
            if len(tag) < 2 or not is_hex64(tag[1]):
                return Verdict(False, "10000:bad-p")
    elif kind == 10002:
        relays = [tag for tag in _tags(event, "r") if len(tag) >= 2]
        if not relays or any(not _WS_URL.match(tag[1]) for tag in relays):
            return Verdict(False, "10002:bad-r")

    return Verdict(True, "")


# Backwards-compatible alias (the reference module used the bare name).
validate = validate_event


def revision_of(event: dict) -> int:
    body, ok = _parse_content(event)
    if ok and isinstance(body, dict) and isinstance(body.get("revision"), int):
        return body["revision"]
    return 0


def declares_revision(event: dict) -> bool:
    body, ok = _parse_content(event)
    return ok and isinstance(body, dict) and "revision" in body


def _content_key(event: dict) -> str:
    """Canonical comparison key for 'would these fold to the same fact?'."""
    body, ok = _parse_content(event)
    if not ok or not isinstance(body, dict):
        return ""
    relevant = {k: v for k, v in body.items() if k not in ("revision", "updated_by", "reason")}
    return json.dumps(relevant, sort_keys=True, separators=(",", ":"))


def fold_events(kind: int, events: list[dict]) -> Any:
    from .fold import FoldResult, fold

    return fold(kind, events)