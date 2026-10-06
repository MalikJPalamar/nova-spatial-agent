"""gemini-live adapter (current Nova path), STUB.

Real version: consumes Gemini Live text turns. Stub: replays a fixture of
{offset_s, text, kind?, confidence?} turns so the contract can be tested
without a network call or any video.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Iterator

from perception.contract import PerceptionEvent


class GeminiLiveAdapter:
    id = "gemini-live"

    def __init__(self, start: dt.datetime | None = None):
        self.start = start or dt.datetime(2026, 10, 6, tzinfo=dt.timezone.utc)

    def events(self, source_input: object) -> Iterator[PerceptionEvent]:
        for line in Path(str(source_input)).read_text().splitlines():
            if not line.strip():
                continue
            t = json.loads(line)
            yield PerceptionEvent(
                ts=(self.start + dt.timedelta(seconds=float(t["offset_s"]))).isoformat(),
                kind=t.get("kind", "observe"),
                text=t["text"].strip(),
                confidence=float(t.get("confidence", 0.7)),
                source=self.id,
            )
