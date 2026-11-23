import copy
import json
import unittest
from pathlib import Path

from apollo_agc.optimization import format_optimization, load_optimization, validate

TEMPLATE = Path(__file__).parents[1] / "optimizations" / "proposal.template.json"


class OptimizationTest(unittest.TestCase):
    def setUp(self):
        self.report = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def test_proposal_truthfully_reports_unmeasured_values(self):
        output = format_optimization(load_optimization(TEMPLATE))
        self.assertIn("memory_words: unmeasured", output)
        self.assertIn("emulator: not_run", output)

    def test_measurements_require_valid_integers_and_evidence(self):
        self.report["status"] = "measured"
        with self.assertRaisesRegex(ValueError, "measured metric"):
            validate(self.report)
        self.report["memory_words"] = {
            "original": True,
            "modified": 1,
            "evidence": "run 1",
        }
        with self.assertRaisesRegex(ValueError, "nonnegative integer"):
            validate(self.report)
        self.report["memory_words"]["original"] = 2
        validate(self.report)

    def test_verified_requires_both_test_records_to_pass(self):
        self.report["status"] = "verified"
        self.report["execution_mct"] = {
            "original": 3,
            "modified": 2,
            "evidence": "cycle trace",
        }
        self.report["equivalence"] = {"result": "pass", "evidence": "boundary vectors"}
        with self.assertRaisesRegex(ValueError, "passing equivalence and emulator"):
            validate(self.report)
        self.report["emulator"] = {"result": "pass", "evidence": "captured run"}
        validate(self.report)
        missing_evidence = copy.deepcopy(self.report)
        del missing_evidence["emulator"]["evidence"]
        with self.assertRaisesRegex(ValueError, "evidence reference"):
            validate(missing_evidence)
