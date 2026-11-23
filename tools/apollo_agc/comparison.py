"""Compare recognizable statements in two AGC source files."""

from collections import Counter
from pathlib import Path

from .source import SourceLine, parse_source, read_text

INSTRUCTION_KINDS = {"instruction", "interpretive"}


def statement(line: SourceLine) -> tuple:
    return line.kind, line.label, line.relative_label, line.operation, line.operands


def unmatched(lines: list[SourceLine], available: Counter) -> list[dict]:
    changes = []
    for line in lines:
        key = statement(line)
        if available[key]:
            available[key] -= 1
        else:
            changes.append(
                {
                    "line": line.number,
                    "kind": line.kind,
                    "label": line.label,
                    "relative_label": line.relative_label,
                    "operation": line.operation,
                    "operands": list(line.operands),
                }
            )
    return changes


def comparison_structure(lines: list[SourceLine]) -> list:
    return [
        None if line.kind in INSTRUCTION_KINDS else statement(line)
        for line in lines
        if line.kind not in ("comment", "blank")
    ]


def compare(before: Path, after: Path) -> dict:
    old = parse_source(read_text(before))
    new = parse_source(read_text(after))
    old_instructions = [line for line in old if line.kind in INSTRUCTION_KINDS]
    new_instructions = [line for line in new if line.kind in INSTRUCTION_KINDS]
    old_sequence = list(map(statement, old_instructions))
    new_sequence = list(map(statement, new_instructions))
    return {
        "before": str(before),
        "after": str(after),
        "source_lines": {"before": len(old), "after": len(new)},
        "instructions": {"before": len(old_sequence), "after": len(new_sequence)},
        "added": unmatched(new_instructions, Counter(old_sequence)),
        "removed": unmatched(old_instructions, Counter(new_sequence)),
        "instruction_sequence_changed": old_sequence != new_sequence,
        "statement_structure_changed": comparison_structure(old)
        != comparison_structure(new),
        "comment_text_changed": (
            [line.comment for line in old if line.comment is not None]
            != [line.comment for line in new if line.comment is not None]
        ),
    }


def format_comparison(report: dict) -> str:
    lines = [f"{report['before']} -> {report['after']}"]
    lines.append(
        f"Source lines: {report['source_lines']['before']} -> {report['source_lines']['after']}"
    )
    lines.append(
        f"Instruction statements: {report['instructions']['before']} -> "
        f"{report['instructions']['after']}"
    )
    for key, marker in (("removed", "-"), ("added", "+")):
        for item in report[key]:
            fields = (
                item["label"],
                item["relative_label"],
                item["operation"],
                *item["operands"],
            )
            lines.append(
                f"{marker} line {item['line']}: "
                + " ".join(field for field in fields if field)
            )
    if report["instruction_sequence_changed"] and not (
        report["added"] or report["removed"]
    ):
        lines.append("Instruction statements were reordered.")
    if report["statement_structure_changed"]:
        lines.append("Statement layout or non-instruction statements changed.")
    if report["comment_text_changed"]:
        lines.append("Comment text changed.")
    return "\n".join(lines)
