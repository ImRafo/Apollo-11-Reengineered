import contextlib
import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from apollo_agc.cli import main
from apollo_agc.comparison import compare

BEFORE = Path("before.agc")
AFTER = Path("after.agc")


class ComparisonTest(unittest.TestCase):
    def compare(self, before, after):
        with patch("apollo_agc.comparison.read_text", side_effect=[before, after]):
            return compare(BEFORE, AFTER)

    def test_duplicate_instructions_are_counted(self):
        report = self.compare(
            "        CA A\n        CA A\n        TC Q",
            "        CA A\n        EXTEND\n        TC Q",
        )
        self.assertEqual(
            [(item["line"], item["operation"]) for item in report["removed"]],
            [(2, "CA")],
        )
        self.assertEqual(
            [(item["line"], item["operation"]) for item in report["added"]],
            [(2, "EXTEND")],
        )

    def test_reordering_preserves_counts(self):
        report = self.compare(
            "        TC Q\n        CA A", "        CA A\n        TC Q"
        )
        self.assertEqual((report["added"], report["removed"]), ([], []))
        self.assertTrue(report["instruction_sequence_changed"])

    def test_formatting_and_comments_leave_statements_equal(self):
        report = self.compare("LOOP\tTC Q # old", "\nLOOP    TC     Q # new")
        self.assertFalse(report["instruction_sequence_changed"])
        self.assertFalse(report["statement_structure_changed"])
        self.assertTrue(report["comment_text_changed"])

    def test_directive_placement_and_relative_labels_are_retained(self):
        report = self.compare(
            "\tSETLOC 4000\n +1\tTC Q",
            " +2\tTC Q\n\tSETLOC 4000",
        )
        self.assertTrue(report["statement_structure_changed"])
        self.assertEqual(report["removed"][0]["relative_label"], "+1")
        self.assertEqual(report["added"][0]["relative_label"], "+2")

    def test_public_cli_json(self):
        fixture = Path(__file__).parent / "fixtures" / "source" / "example.agc"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = main(["compare", str(fixture), str(fixture), "--format", "json"])
        report = json.loads(output.getvalue())
        self.assertEqual(status, 0)
        self.assertEqual(report["instructions"], {"before": 5, "after": 5})
        self.assertEqual(report["added"], [])
