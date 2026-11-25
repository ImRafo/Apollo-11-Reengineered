import unittest
from pathlib import Path

from scripts.optimization_cases import parse_experiment
from scripts.optimization_probe import OUTPUTS, Observation, compare, encode_inputs


class ProbeComparisonTest(unittest.TestCase):
    def setUp(self):
        self.experiment = parse_experiment(
            Path("experiment.toml"),
            {
                "title": "Example",
                "origin": "Example",
                "scope": "Example",
                "expected": "counterexample",
                "inputs": {"x": [0, 0o77777]},
            },
        )

    def test_encodes_raw_input_words(self):
        self.assertEqual(
            encode_inputs(self.experiment),
            "0 0 4321 0 0 0 0 0\n0 0 4321 77777 0 0 0 0\n",
        )

    def test_counts_cycle_savings_and_reports_distinct_zero_signs(self):
        fields = (0,) * len(OUTPUTS)
        baseline = [Observation(5, fields)] * 2
        candidate = [Observation(3, fields), Observation(4, (0o177777, *fields[1:]))]
        summary = compare(self.experiment, baseline, candidate)
        self.assertTrue(summary["matches_expectation"])
        self.assertEqual(summary["mct_saved_histogram"], {1: 1, 2: 1})
        self.assertEqual(summary["differing_vectors"], 1)
        example = summary["first_counterexample"]
        self.assertEqual(example["input"]["x"], "077777")
        self.assertEqual(example["different_fields"], ["a"])
        self.assertEqual(example["baseline"]["a"], "000000")
        self.assertEqual(example["candidate"]["a"], "177777")

    def test_missing_observations_are_errors(self):
        row = Observation(2, (0,) * len(OUTPUTS))
        with self.assertRaises(ValueError):
            compare(self.experiment, [row], [row])
