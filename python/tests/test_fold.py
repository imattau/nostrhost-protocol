"""Fold behaviour tests (envelope.md §3): revision wins, conflicts, revocation."""

from __future__ import annotations

import nostrhost_protocol as p


def _capability(ev_id: str, d: str, rev: int, created: int, scopes: list[str]) -> dict:
    return {
        "id": ev_id,
        "kind": 31100,
        "created_at": created,
        "tags": [["d", d]],
        "content": '{"type":"agent","scopes":%s,"revision":%d}' % (str(scopes).replace("'", '"'), rev),
    }


def test_higher_revision_wins_even_if_older():
    d = "a" * 64
    events = [
        _capability("a" * 64, d, 2, 100, ["app.read"]),
        _capability("b" * 64, d, 1, 500, ["app.read", "old"]),
    ]
    result = p.fold_events(31100, events)
    assert result.revision == 2
    assert result.fact == {"type": "agent", "scopes": ["app.read"]}
    assert result.conflicts == 0


def test_equal_revision_tie_break_and_conflict():
    d = "b" * 64
    events = [
        _capability("c" * 64, d, 1, 500, ["app.read"]),
        _capability("d" * 64, d, 1, 100, ["app.read", "old"]),
    ]
    result = p.fold_events(31100, events)
    assert result.revision == 1
    assert result.fact["scopes"] == ["app.read"]
    assert result.conflicts == 1


def test_invalid_events_are_ignored():
    d = "e" * 64
    events = [
        {"id": "f" * 64, "kind": 31100, "created_at": 100, "tags": [], "content": ""},
        _capability("e" * 64, d, 1, 100, ["app.read"]),
    ]
    result = p.fold_events(31100, events)
    assert result.revision == 1


def test_empty_inputs_yield_default_fold():
    result = p.fold_events(31100, [])
    assert result.subject == ""
    assert result.revision == 0
    assert result.enabled is True


def test_enabled_false_semantic_revocation():
    d = "0f" * 32
    events = [
        {
            "id": "h" * 64,
            "kind": 31102,
            "created_at": 100,
            "tags": [["d", d]],
            "content": '{"username":"alice","signer_type":"nip07","enabled":false,"revision":2}',
        },
        {
            "id": "i" * 64,
            "kind": 31102,
            "created_at": 50,
            "tags": [["d", d]],
            "content": '{"username":"alice","signer_type":"nip07","enabled":true,"revision":1}',
        },
    ]
    result = p.fold_events(31102, events)
    assert result.enabled is False
    assert result.revision == 2