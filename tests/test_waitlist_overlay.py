import unittest

from scripts.waitlist_overlay import (
    DISPATCH_PATHS,
    ORIGINAL,
    REPLACEMENT,
    replace_dispatch,
)


class WaitlistOverlayTest(unittest.TestCase):
    def test_dispatch_groups_partition_the_entire_high_word_domain(self):
        cases = [value for _, values, _, _ in DISPATCH_PATHS for value in values]
        self.assertEqual(sorted(cases), list(range(0o100000)))
        targets = {name: stop for name, _, stop, _ in DISPATCH_PATHS}
        self.assertEqual(targets["positive_zero"], targets["negative_zero"])

    def setUp(self):
        self.original = b"".join(
            b"\t\t" + b"\t".join(tokens) + b"\r\n" for tokens in ORIGINAL
        )
        self.replacement = REPLACEMENT.read_bytes()

    def test_replaces_only_the_five_dispatch_rows(self):
        before, after = b"BEFORE\r\n\r\n", b" +2\t\tCA\tLONGTIME +1\r\n"
        result = replace_dispatch(before + self.original + after, self.replacement)
        self.assertTrue(result.startswith(before))
        self.assertTrue(result.endswith(after))
        self.assertEqual(
            len(result.splitlines()), len((before + self.original + after).splitlines())
        )
        self.assertIn(b"CCS     LONGTIME", result)
        self.assertEqual(result.count(b"\r\n"), result.count(b"\n"))

    def test_refuses_drift_or_an_ambiguous_block(self):
        for source in (self.original.replace(b"LONGPOOH", b"WRONG"), self.original * 2):
            with (
                self.subTest(source=source),
                self.assertRaisesRegex(ValueError, "one unchanged"),
            ):
                replace_dispatch(source, self.replacement)

    def test_refuses_a_variant_that_relocates_following_words(self):
        with self.assertRaisesRegex(ValueError, "five instruction rows"):
            replace_dispatch(self.original, b"\t\tCCS LONGTIME\n")
