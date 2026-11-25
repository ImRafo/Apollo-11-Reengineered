"""Measure emulator checkpoints and compare raw AGC state."""

import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

if __package__:
    from .optimization_cases import INPUTS, Experiment
else:
    from optimization_cases import INPUTS, Experiment

OUTPUTS = (*INPUTS, "eb", "fb", "bb", "index", "extracode", "interrupts")


@dataclass(frozen=True)
class Observation:
    mct: int
    state: tuple[int, ...]


def encode_inputs(experiment: Experiment) -> str:
    return "".join(
        " ".join(f"{value:o}" for value in case) + "\n" for case in experiment.vectors()
    )


def measure(
    harness: Path, rope: Path, entry: int, stop: int, inputs: str
) -> list[Observation]:
    result = subprocess.run(
        [harness, rope, f"{entry:o}", f"{stop:o}"],
        capture_output=True,
        text=True,
        input=inputs,
        check=False,
        timeout=60,
    )
    if result.returncode:
        message = result.stderr.strip() or f"agc_probe exited {result.returncode}"
        raise ValueError(f"{rope} ({entry:04o} to {stop:04o}): {message}")

    output = []
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) != 1 + len(OUTPUTS):
            raise ValueError(f"unexpected agc_probe row: {line}")
        output.append(
            Observation(int(fields[0]), tuple(int(field, 8) for field in fields[1:]))
        )
    if not output:
        raise ValueError("agc_probe returned no checkpoint observations")
    return output


def raw_state(fields, values) -> dict[str, str]:
    return {field: f"{value:06o}" for field, value in zip(fields, values, strict=True)}


def compare(
    experiment: Experiment, baseline: list[Observation], candidate: list[Observation]
) -> dict:
    baseline_counts: Counter[int] = Counter()
    candidate_counts: Counter[int] = Counter()
    savings: Counter[int] = Counter()
    differing = 0
    example = None
    for case, before, after in zip(
        experiment.vectors(), baseline, candidate, strict=True
    ):
        baseline_counts[before.mct] += 1
        candidate_counts[after.mct] += 1
        savings[before.mct - after.mct] += 1
        if before.state != after.state:
            differing += 1
            if example is None:
                example = {
                    "input": raw_state(INPUTS, case),
                    "baseline": raw_state(OUTPUTS, before.state),
                    "candidate": raw_state(OUTPUTS, after.state),
                    "different_fields": [
                        name
                        for name, old, new in zip(
                            OUTPUTS, before.state, after.state, strict=True
                        )
                        if old != new
                    ],
                }
    outcome = "counterexample" if differing else "match"
    return {
        "vectors": sum(baseline_counts.values()),
        "differing_vectors": differing,
        "outcome": outcome,
        "matches_expectation": outcome == experiment.expected,
        "baseline_mct_histogram": dict(sorted(baseline_counts.items())),
        "candidate_mct_histogram": dict(sorted(candidate_counts.items())),
        "mct_saved_histogram": dict(sorted(savings.items())),
        "first_counterexample": example,
    }
