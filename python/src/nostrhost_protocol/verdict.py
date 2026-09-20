"""Validation verdict type."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Verdict:
    """Outcome of :func:`validate_event` plus a stable reason code.

    ``ok`` is True when the event is accepted; ``code`` is non-empty exactly
    when the event is rejected (the first failing rule, see
    ``spec/envelope.md`` §2).
    """

    ok: bool
    code: str = ""

    def as_dict(self) -> dict:
        return {"accept": self.ok, "code": self.code}