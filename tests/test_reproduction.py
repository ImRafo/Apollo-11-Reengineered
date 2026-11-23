import unittest

from scripts.reproduce_luminary import ROPE_BYTES, WORDS_PER_BANK, compare_ropes


class ReproductionTest(unittest.TestCase):
    def test_equal_encoded_images(self):
        image = bytes(ROPE_BYTES)
        result = compare_ropes(image, image)
        self.assertTrue(result["byte_identical"])
        self.assertEqual(result["assembled_sha256"], result["reference_sha256"])

    def test_difference_locations_use_dump_bank_order(self):
        reference = bytes(ROPE_BYTES)
        actual = bytearray(reference)
        actual[1] = 1
        actual[WORDS_PER_BANK * 4 + 2] = 1
        result = compare_ropes(actual, reference)
        self.assertFalse(result["byte_identical"])
        self.assertEqual(result["differences_by_bank"], {"00": 1, "02": 1})
        self.assertEqual(result["first_differences"][1]["offset"], "0001")
        self.assertEqual(
            result["first_differences"][0]["assembled_encoded_word"], "000001"
        )

    def test_rejects_truncated_rope(self):
        with self.assertRaisesRegex(ValueError, "73728"):
            compare_ropes(b"", bytes(ROPE_BYTES))
