"""onestreamer adapter (future, local model), STUB.

Real version: wraps OneStreamer's StreamingSession and maps its outputs:
</Response> text -> kind=observe, PHCM captions -> kind=summary,
</Silence> | </Standby> -> kind=state. Stub: maps a OneStreamer-1M
`onestreamer-public-meta-v1` record's timeline to the same events, so the
contract and the replay harness (A3) work with no weights and no media.
"""
from __future__ import annotations

import datetime as dt
from typing import Iterator

from perception.contract import PerceptionEvent


class OneStreamerAdapter:
    id = "onestreamer"

    def __init__(self, start: dt.datetime | None = None):
        self.start = start or dt.datetime(2026, 10, 6, tzinfo=dt.timezone.utc)

    def events(self, source_input: object) -> Iterator[PerceptionEvent]:
        rec = source_input  # one decoded OneStreamer-1M record
        fps = float(rec["sequence"]["fps"])
        rid = rec.get("id", "rec").replace(":", ".")
        at = lambda tick: (self.start + dt.timedelta(seconds=tick / fps)).isoformat()  # noqa: E731
        for e in rec.get("timeline", []):
            typ = e.get("type")
            if typ == "response":
                yield PerceptionEvent(ts=at(e["at"]), kind="observe", text=e["text"].strip(), confidence=0.9, source=f"{self.id}:{rid}")
            elif typ in ("silence", "standby"):
                tick = e["interval"][0] if "interval" in e else e.get("at", 0)
                yield PerceptionEvent(ts=at(tick), kind="state", text=typ, confidence=1.0, source=f"{self.id}:{rid}")
