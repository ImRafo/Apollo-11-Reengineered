"""Validate and render evidence records for proposed AGC changes."""

import json
from pathlib import Path

from .source import read_text

TEXT_FIELDS = (
    "routine",
    "rationale",
    "original_code",
    "modified_code",
    "limitations",
)
METRICS = ("memory_words", "execution_mct")
TESTS = ("equivalence", "emulator")
STATUSES = {"proposed", "measured", "verified", "rejected"}


def nonempty(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate(report: dict) -> None:
    if not isinstance(report, dict) or type(report.get("schema_version")) is not int:
        raise ValueError(
            "expected an optimization report object with an integer schema_version"
        )
    if report["schema_version"] != 1:
        raise ValueError("unsupported optimization report schema version")
    for field in TEXT_FIELDS:
        if not nonempty(report.get(field)):
            raise ValueError(f"{field} must be a nonempty string")
    status = report.get("status")
    if not isinstance(status, str) or status not in STATUSES:
        raise ValueError("status must be proposed, measured, verified or rejected")

    measured = 0
    for field in METRICS:
        if field not in report:
            raise ValueError(f"missing {field}; use null when unmeasured")
        metric = report[field]
        if metric is None:
            continue
        if not isinstance(metric, dict) or not nonempty(metric.get("evidence")):
            raise ValueError(f"{field} requires an evidence reference")
        for variant in ("original", "modified"):
            value = metric.get(variant)
            if type(value) is not int or value < 0:
                raise ValueError(f"{field}.{variant} must be a nonnegative integer")
        measured += 1

    for field in TESTS:
        test = report.get(field)
        if not isinstance(test, dict):
            raise ValueError(f"{field} must be a test result object")
        result = test.get("result")
        if result not in ("not_run", "pass", "fail"):
            raise ValueError(f"{field}.result must be not_run, pass or fail")
        if result != "not_run" and not nonempty(test.get("evidence")):
            raise ValueError(f"{field} requires an evidence reference for {result}")

    if status in ("measured", "verified") and not measured:
        raise ValueError(f"{status} reports require a measured metric")
    if status == "verified" and any(report[test]["result"] != "pass" for test in TESTS):
        raise ValueError(
            "verified reports require passing equivalence and emulator evidence"
        )


def load_optimization(path: Path) -> dict:
    data = read_text(path)
    try:
        report = json.loads(data)
        validate(report)
    except ValueError as error:
        raise ValueError(f"{path}: {error}") from error
    return report


def format_optimization(report: dict) -> str:
    lines = [f"{report['routine']} [{report['status']}]", report["rationale"]]
    for variant in ("original", "modified"):
        lines.extend((f"\n{variant.title()} code", report[f"{variant}_code"]))
    for field in METRICS:
        metric = report[field]
        if metric is None:
            lines.append(f"{field}: unmeasured")
        else:
            lines.append(
                f"{field}: {metric['original']} -> {metric['modified']} ({metric['evidence']})"
            )
    for field in TESTS:
        test = report[field]
        detail = f" ({test['evidence']})" if test.get("evidence") else ""
        lines.append(f"{field}: {test['result']}{detail}")
    lines.append(f"Limitations: {report['limitations']}")
    return "\n".join(lines)
