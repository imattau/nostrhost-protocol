# nostrhost-protocol

Cross-language library for the NostrHost control-plane event protocol: a
language-neutral specification plus standalone Python and Go bindings.

Extracted from the umbrella superproject's `authority/event-protocol` (the
frozen contract), the Python reference (`tools/event_protocol.py`) and the Go
relay's `internal/eventmodel` / `internal/eventprotocol` packages. Wire formats,
validation order, stable rejection codes, folds and persisted state are
unchanged.

## Layout

```
spec/     language-neutral specification: envelope rules, JSON Schemas, the
          machine-readable kind manifest (manifest.json), and the verdict /
          fold conformance fixtures (authoritative)
python/   installable `nostrhost-protocol` Python package
go/       Go module github.com/imattau/nostrhost-protocol/go (go-nostr events)
```

## The protocol

- `spec/envelope.md` — normative validation order, revision/conflict/fold and
  revocation rules, schema-version compatibility policy.
- `spec/manifest.json` — machine-readable event-name → kind → category →
  schema-version → schema-reference → stable-rejection-codes registry.
- `spec/schemas/*.json` — JSON Schema (draft-07) per documented kind.
- `spec/fixtures/verdicts.json`, `spec/fixtures/folds.json` — the conformance
  corpus. Both bindings must reach identical results (the corpus is the source
  of truth).

## Bindings

Python:

```python
from nostrhost_protocol import Verdict, FoldResult, validate_event, fold_events, Kind

v = validate_event(event_dict)          # Verdict(ok, code)
r = fold_events(31100, [event_dict])    # FoldResult(...)
```

Go:

```go
import protocol "github.com/imattau/nostrhost-protocol/go"

v := protocol.Validate(nostrEvent)          // protocol.Verdict
r := protocol.Fold(31100, []*nostr.Event{}) // protocol.FoldResult
```

Each binding embeds the spec (schemas + fixtures) so it installs and tests
independently, with drift tests that pin the embedded copies to `spec/`.

## Conformance

- `cd python && uv run pytest -q`
- `cd go && go test ./...`

## License

AGPL-3.0-or-later.