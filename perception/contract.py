"""PerceptionSource contract (WO-038 A1).

A perception adapter turns some sensor stream into PerceptionEvents: plain text
with a timestamp, a kind (observe | summary | state), a confidence and a source.
Raw media never crosses this interface; only events do. Adapters are bodies
(R2): swap one for another without touching the gate or the inbox.

Stdlib only, so the contract can be validated anywhere without dependencies.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Iterator, Protocol

KINDS = ("observe", "summary", "state")
SOURCE_RE = re.compile(r"^[a-z0-9-]+(:[A-Za-z0-9._-]+)?$")
SCHEMA_PATH = Path(__file__).with_name("event.schema.json")


@dataclass(frozen=True)
class PerceptionEvent:
    ts: str
    kind: str
    text: str
    confidence: float
    source: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


class SchemaError(ValueError):
    pass


def validate(obj: dict) -> PerceptionEvent:
    """Validate a decoded event against event.schema.json's rules (stdlib re-implementation)."""
    schema = json.loads(SCHEMA_PATH.read_text())
    required = set(schema["required"])
    allowed = set(schema["properties"])
    if not isinstance(obj, dict):
        raise SchemaError("event must be an object")
    missing, extra = required - obj.keys(), obj.keys() - allowed
    if missing:
        raise SchemaError(f"missing {sorted(missing)}")
    if extra:
        raise SchemaError(f"unexpected {sorted(extra)}")
    try:
        t = dt.datetime.fromisoformat(obj["ts"])
    except (TypeError, ValueError) as e:
        raise SchemaError(f"ts not ISO-8601: {obj['ts']!r}") from e
    if t.tzinfo is None:
        raise SchemaError("ts must carry a timezone")
    if obj["kind"] not in KINDS:
        raise SchemaError(f"kind must be one of {KINDS}")
    if not isinstance(obj["text"], str) or not (1 <= len(obj["text"]) <= 2000):
        raise SchemaError("text must be 1-2000 chars")
    c = obj["confidence"]
    if isinstance(c, bool) or not isinstance(c, (int, float)) or not 0 <= c <= 1:
        raise SchemaError("confidence must be a number in [0,1]")
    if not isinstance(obj["source"], str) or not SOURCE_RE.match(obj["source"]):
        raise SchemaError(f"bad source {obj['source']!r}")
    return PerceptionEvent(**obj)


class PerceptionSource(Protocol):
    """Every adapter implements this: given an input (fixture, stream handle), yield events."""

    id: str

    def events(self, source_input: object) -> Iterator[PerceptionEvent]: ...


def write_inbox(events: Iterable[PerceptionEvent], inbox: Path) -> int:
    """Append events as JSONL to the inbox file (the Tier 3 inbox, WO-008→037, is the real target)."""
    inbox.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with inbox.open("a", encoding="utf-8") as f:
        for e in events:
            validate(json.loads(e.to_json()))
            f.write(e.to_json() + "\n")
            n += 1
    return n
