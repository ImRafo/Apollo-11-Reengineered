import unittest
from pathlib import Path

from apollo_agc.source import parse_source

FIXTURE = Path(__file__).parent / "fixtures" / "source" / "example.agc"


class SourceTest(unittest.TestCase):
    def test_representative_source(self):
        lines = parse_source(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(
            [line.kind for line in lines],
            [
                "comment",
                "comment",
                "blank",
                "directive",
                "directive",
                "instruction",
                "instruction",
                "instruction",
                "interpretive",
                "continuation",
                "instruction",
                "label",
                "include",
                "unrecognized",
                "malformed",
            ],
        )
        self.assertEqual(lines[5].label, "LOOP")
        self.assertEqual(lines[5].operands, ("1/4",))
        self.assertEqual(lines[5].comment, "Inline comment")
        self.assertIsNone(lines[10].label)
        self.assertEqual(lines[12].operands, ("other.agc",))

    def test_column_one_is_a_label_even_when_named_like_an_opcode(self):
        label, instruction = parse_source("TC\n\tTC Q\n")
        self.assertEqual(label.label, "TC")
        self.assertEqual(label.kind, "label")
        self.assertEqual(instruction.kind, "instruction")
        self.assertEqual(instruction.number, 2)

    def test_line_endings_and_no_trailing_newline(self):
        self.assertEqual(
            [line.kind for line in parse_source("\r\n# c\r\tCA A")],
            [
                "blank",
                "comment",
                "instruction",
            ],
        )
        self.assertEqual(len(parse_source("\n")), 1)
        self.assertEqual(parse_source(""), [])

    def test_malformed_lines_are_reported_and_analysis_continues(self):
        lines = parse_source("bad!\tCA A\n\tADS\x00\n$two files\n\tAD A")
        self.assertEqual(
            [line.kind for line in lines],
            [
                "malformed",
                "malformed",
                "malformed",
                "instruction",
            ],
        )
        self.assertEqual(lines[1].issue, "control character")
