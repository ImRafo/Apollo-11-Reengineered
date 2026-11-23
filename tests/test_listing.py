import contextlib
import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from apollo_agc.cli import main
from apollo_agc.listing import parse_listing


def listing(*records, modified_extent=None, suffix=""):
    counts = {1: 5, 2: 2}
    counts.update(modified_extent or {})
    rows = "\n".join(
        f"Bank {bank:02o}:  {counts.get(bank, 0):04o}/2000 words used."
        for bank in range(36)
    )
    return "\n".join(
        (
            "Apollo Guidance Computer (AGC) assembler, version test, built today, target AGC4",
            *records,
            "Usage Table for Fixed-Memory Banks",
            rows,
            "Unresolved symbols:  0",
            "Fatal errors:  0",
            "Multiply-defined symbols:  0",
            suffix,
        )
    )


def word_row(pc, first="", second="", label_value=""):
    return f"000001,000001: {pc:>7}  {label_value:>7}  {first:<6}{second:<6} LABEL"


class ListingTest(unittest.TestCase):
    def test_accepts_native_windows_line_endings(self):
        self.assertEqual(len(parse_listing(listing().replace("\n", "\r\n"))), 36)

    def test_reads_only_object_word_columns_and_includes_the_checksum(self):
        banks = parse_listing(
            listing(
                word_row("01,2000", label_value="0040000"),
                word_row("01,2001", "00000", "12345"),
                word_row("01,2002", "12345"),
                word_row("4000", "54321"),
                word_row("E7,1600", "77777"),
                suffix="Bugger word 00002 at 01,2007.",
            )
        )
        self.assertEqual(len(banks), 36)
        self.assertEqual(banks[1]["occupied_words"], 3)
        self.assertEqual(banks[1]["checksum_offset"], "0007")
        self.assertEqual(
            banks[1]["occupied_ranges"], [["0001", "0002"], ["0007", "0007"]]
        )
        self.assertEqual(banks[2]["occupied_ranges"], [["0000", "0000"]])

    def test_rejects_missing_table_and_bad_assembly_summary(self):
        with self.assertRaisesRegex(ValueError, "usage rows"):
            parse_listing(listing().replace("Bank 43:", "Other:"))
        with self.assertRaisesRegex(ValueError, "fatal errors"):
            parse_listing(listing().replace("Fatal errors:  0", "Fatal errors:  1"))
        with self.assertRaisesRegex(ValueError, "AGC4"):
            parse_listing(listing().replace("AGC4", "BLK2"))

    def test_rejects_cross_bank_and_invalid_word_rows(self):
        with self.assertRaisesRegex(ValueError, "cross"):
            parse_listing(
                listing(
                    word_row("01,3777", "12345", "54321"), modified_extent={1: 0o2000}
                )
            )
        with self.assertRaisesRegex(ValueError, "object word"):
            parse_listing(listing(word_row("4000", "?????")))

    def test_json_through_cli(self):
        path = Path("output.lst")
        output = io.StringIO()
        with (
            patch("apollo_agc.listing.read_text", return_value=listing()),
            contextlib.redirect_stdout(output),
        ):
            status = main(["memory", str(path), "--format", "json"])
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(output.getvalue())["target"], "AGC4")
