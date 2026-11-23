"""Summaries of physical AGC source lines."""

from collections import Counter
from pathlib import Path

from .source import parse_source, read_text

OPERATIONS = ("instruction", "interpretive", "directive", "unrecognized")
LINE_KINDS = (
    "blank",
    "comment",
    "label",
    "include",
    "continuation",
    "malformed",
    *OPERATIONS,
)


def analyze_file(path: Path) -> dict:
    lines = parse_source(read_text(path))
    counts = Counter(line.kind for line in lines)
    operations = {
        kind: dict(
            sorted(
                Counter(line.operation for line in lines if line.kind == kind).items()
            )
        )
        for kind in OPERATIONS
    }
    return {
        "path": str(path),
        "lines": len(lines),
        "counts": {kind: counts[kind] for kind in LINE_KINDS},
        "labels": sum(line.label is not None for line in lines),
        "inline_comments": sum(
            line.comment is not None and line.kind != "comment" for line in lines
        ),
        "operations": operations,
        "includes": [line.operands[0] for line in lines if line.kind == "include"],
        "diagnostics": [
            {"line": line.number, "message": line.issue}
            for line in lines
            if line.issue is not None
        ],
    }


def analyze(paths: list[Path]) -> dict:
    files = []
    for path in paths:
        if path.is_dir():
            sources = sorted(file for file in path.glob("*.agc") if file.is_file())
            if not sources:
                raise ValueError(f"{path}: no .agc files")
            files.extend(analyze_file(file) for file in sources)
        else:
            files.append(analyze_file(path))
    return {
        "files": files,
        "total_lines": sum(file["lines"] for file in files),
        "totals": {
            kind: sum(file["counts"][kind] for file in files) for kind in LINE_KINDS
        },
    }


def format_analysis(report: dict) -> str:
    output = []
    for file in report["files"]:
        output.append(
            f"{file['path']} ({file['lines']} lines, {file['labels']} labels)"
        )
        output.append(
            "  "
            + ", ".join(f"{count} {kind}" for kind, count in file["counts"].items())
        )
        for kind, counts in file["operations"].items():
            if counts:
                output.append(
                    f"  {kind} mnemonics: "
                    + ", ".join(f"{name} {count}" for name, count in counts.items())
                )
        for diagnostic in file["diagnostics"]:
            output.append(f"  line {diagnostic['line']}: {diagnostic['message']}")
    output.append(
        f"Total: {report['total_lines']} lines in {len(report['files'])} file(s)"
    )
    return "\n".join(output)
