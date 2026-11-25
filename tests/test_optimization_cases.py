import unittest
from pathlib import Path

from scripts.optimization_cases import INPUTS, parse_experiment


class ExperimentCaseTest(unittest.TestCase):
    def parse(self, **inputs):
        return parse_experiment(
            Path("experiment.toml"),
            {
                "title": "Example",
                "origin": "Floating example",
                "scope": "One path",
                "expected": "match",
                "inputs": inputs,
            },
        )

    def test_signed_zero_and_overflow_survive_input_encoding(self):
        cases = list(self.parse(a=[0, 0o177777, 0o40000], x=[0o77777]).vectors())
        self.assertEqual(
            [dict(zip(INPUTS, row, strict=True))["a"] for row in cases],
            [0, 0o177777, 0o40000],
        )
        self.assertEqual(cases[0], (0, 0, 0o4321, 0o77777, 0, 0, 0, 0))

    def test_exhaustive_word_axis_includes_both_zeros_and_all_patterns(self):
        axis = self.parse(x="all").axes[3]
        self.assertEqual(len(axis), 32768)
        self.assertEqual((axis[0], axis[-1]), (0, 0o77777))

    def test_rejects_unsafe_or_confusing_grids(self):
        for bad in (
            {"z": [0]},
            {"l": [0o100000]},
            {"a": [True]},
            {"x": [0, 0]},
            {"x": "all", "y": "all"},
            {"x": []},
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.parse(**bad)
