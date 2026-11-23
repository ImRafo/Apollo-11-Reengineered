import contextlib
import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from apollo_agc.cli import main
from apollo_agc.source import read_text

FIXTURE = Path(__file__).parent / "fixtures" / "source" / "example.agc"


class AnalysisCliTest(unittest.TestCase):
    def invoke(self, *arguments):
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            code = main(list(arguments))
        return code, output.getvalue(), errors.getvalue()

    def test_json_reports_counts_and_diagnostics(self):
        code, output, errors = self.invoke("analyze", str(FIXTURE), "--format", "json")
        payload = json.loads(output)
        self.assertEqual((code, errors), (0, ""))
        self.assertEqual(payload["total_lines"], 15)
        self.assertEqual(sum(payload["totals"].values()), 15)
        self.assertEqual(payload["files"][0]["labels"], 4)
        self.assertEqual(payload["files"][0]["includes"], ["other.agc"])
        self.assertEqual(payload["files"][0]["operations"]["instruction"]["TC"], 1)
        self.assertEqual(payload["files"][0]["diagnostics"][0]["line"], 15)

    def test_text_and_strict_mode(self):
        code, output, errors = self.invoke("analyze", str(FIXTURE.parent), "--strict")
        self.assertEqual((code, errors), (1, ""))
        self.assertIn("line 15: invalid include", output)
        self.assertIn("Total: 15 lines in 1 file(s)", output)

    def test_missing_file(self):
        code, output, errors = self.invoke(
            "analyze", str(FIXTURE.with_name("missing.agc"))
        )
        self.assertEqual((code, output), (1, ""))
        self.assertIn("missing.agc", errors)

    def test_argument_errors_use_exit_two(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                main(["analyze", "--format", "yaml", str(FIXTURE)])
        self.assertEqual(error.exception.code, 2)

    def test_decode_and_read_errors_include_the_path(self):
        path = Path("invalid.agc")
        errors = [
            (
                b"\xff",
                "invalid UTF-8 at byte 0",
            ),
            (PermissionError(13, "Permission denied"), "Permission denied"),
        ]
        for failure, message in errors:
            with (
                self.subTest(failure=failure),
                patch.object(
                    Path,
                    "read_bytes",
                    side_effect=failure if isinstance(failure, OSError) else None,
                    return_value=failure,
                ),
            ):
                with self.assertRaisesRegex(ValueError, message):
                    read_text(path)
                code, output, detail = self.invoke("analyze", str(path))
                self.assertEqual((code, output), (1, ""))
                self.assertIn(str(path), detail)

    def test_utf8_bom_is_accepted_and_error_offsets_include_it(self):
        path = Path("bom.agc")
        with patch.object(
            Path, "read_bytes", return_value=bytes.fromhex("efbbbf") + b"# comment"
        ):
            self.assertEqual(read_text(path), "# comment")
        with patch.object(Path, "read_bytes", return_value=bytes.fromhex("efbbbf41ff")):
            with self.assertRaisesRegex(ValueError, "invalid UTF-8 at byte 4"):
                read_text(path)
