import json
import unittest
from pathlib import Path

from perception.adapters.gemini_live import GeminiLiveAdapter
from perception.adapters.onestreamer import OneStreamerAdapter
from perception.contract import SchemaError, validate, write_inbox

FIX = Path(__file__).resolve().parent.parent / "perception" / "fixtures"


class ContractTest(unittest.TestCase):
    def check_all(self, events):
        events = list(events)
        self.assertTrue(events)
        for e in events:
            validate(json.loads(e.to_json()))
        return events

    def test_gemini_live_fixture_is_schema_valid(self):
        evs = self.check_all(GeminiLiveAdapter().events(FIX / "gemini_live_turns.jsonl"))
        self.assertEqual({e.kind for e in evs}, {"state", "observe", "summary"})

    def test_onestreamer_fixture_is_schema_valid(self):
        n = 0
        for line in (FIX / "onestreamer_1m_sample.jsonl").read_text().splitlines():
            evs = self.check_all(OneStreamerAdapter().events(json.loads(line)))
            self.assertTrue(any(e.kind == "observe" for e in evs))
            n += 1
        self.assertEqual(n, 5)

    def test_rejects_bad_events(self):
        good = {"ts": "2026-10-06T00:00:00+00:00", "kind": "observe", "text": "x", "confidence": 0.5, "source": "gemini-live"}
        validate(good)
        for bad in (
            {**good, "kind": "video"},
            {**good, "ts": "2026-10-06T00:00:00"},
            {**good, "confidence": 1.5},
            {**good, "frame": "base64..."},
            {k: v for k, v in good.items() if k != "text"},
        ):
            with self.assertRaises(SchemaError):
                validate(bad)

    def test_write_inbox(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            n = write_inbox(GeminiLiveAdapter().events(FIX / "gemini_live_turns.jsonl"), Path(d) / "inbox.jsonl")
            self.assertEqual(n, 3)


if __name__ == "__main__":
    unittest.main()
