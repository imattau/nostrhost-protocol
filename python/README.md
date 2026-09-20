# nostrhost-protocol (Python binding)

Standalone Python binding for the NostrHost control-plane event protocol.

```python
from nostrhost_protocol import (
    Verdict,
    FoldResult,
    validate_event,
    fold_events,
    Kind,
    load_schema,
    load_manifest,
)

v = validate_event(event_dict)          # Verdict(ok, code)
r = fold_events(31100, [event_dict])    # FoldResult(...)

kinds = load_manifest()                 # KindSpec records (kind/name/category/...)
schema = load_schema(31100)             # dict JSON Schema or None
```

The spec (envelope rules, schemas, manifest, conformance fixtures) ships as
package data, so the package installs and tests independently. The authoritative
copy of the spec lives at the repository root under `spec/`; drift tests pin
the bundled copy to it.

Run the conformance corpus:

```python
from nostrhost_protocol import conformance
print(conformance("python"))
```

Requires Python 3.11+. License: AGPL-3.0-or-later.