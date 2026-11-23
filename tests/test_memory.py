import unittest

from apollo_agc.memory import BANK_WORDS, Bank, fixed_address


class MemoryTest(unittest.TestCase):
    def test_banked_fixed_fixed_and_erasable_addresses(self):
        for raw, expected in {
            "02,2000": (2, 0),
            "4000": (2, 0),
            "7777": (3, BANK_WORDS - 1),
            "43,3777": (0o43, BANK_WORDS - 1),
            "E7,1777": None,
            "0177": None,
        }.items():
            with self.subTest(raw=raw):
                self.assertEqual(fixed_address(raw), expected)

    def test_rejects_out_of_bounds_or_ambiguous_addresses(self):
        for raw in ("44,2000", "04,4000", "3000", "10000"):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                fixed_address(raw)

    def test_reports_holes_separately_from_the_tail_and_accounts_for_checksum(self):
        report = Bank(0o10, 5, {0, 1, 4}, checksum=7).report()
        self.assertEqual(report["bank"], "10")
        self.assertEqual(report["occupied_words"], 4)
        self.assertEqual(
            report["occupied_ranges"],
            [["0000", "0001"], ["0004", "0004"], ["0007", "0007"]],
        )
        self.assertEqual(report["unlisted_within_extent"], [["0002", "0003"]])
        self.assertEqual(report["unlisted_tail"], [["0005", "0006"], ["0010", "1777"]])
        self.assertEqual(report["potentially_available_words"], BANK_WORDS - 6)

    def test_full_and_empty_bank_boundaries(self):
        self.assertEqual(Bank(0, 0).report()["potentially_available_words"], BANK_WORDS)
        self.assertEqual(Bank(1, BANK_WORDS).report()["unlisted_tail"], [])
        with self.assertRaisesRegex(ValueError, "outside"):
            Bank(1, BANK_WORDS, {BANK_WORDS}).report()
        with self.assertRaisesRegex(ValueError, "checksum"):
            Bank(1, 1, {0}, checksum=0).report()
