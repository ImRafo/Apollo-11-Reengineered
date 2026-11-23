import unittest
from pathlib import Path

from apollo_agc.analysis import analyze

ROOT = Path(__file__).resolve().parents[1]


class ArchiveTest(unittest.TestCase):
    def test_both_archives_have_readable_source_and_historical_labels(self):
        for program in ("Luminary099", "Comanche055"):
            with self.subTest(program=program):
                report = analyze([ROOT / program])
                self.assertGreater(report["total_lines"], 60_000)
                self.assertEqual(sum(report["totals"].values()), report["total_lines"])
                self.assertEqual(report["totals"]["malformed"], 0)
                self.assertGreater(report["totals"]["instruction"], 10_000)
