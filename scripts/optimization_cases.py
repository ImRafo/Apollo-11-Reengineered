"""Read assembly experiment metadata and generate deterministic input vectors."""

import math
import tomllib
from dataclasses import dataclass
from itertools import product
from pathlib import Path

# Keep the names in the same order as the octal words accepted by agc_probe.c.
INPUTS = {
    "a": (0o177777, 0),
    "l": (0o77777, 0),
    "q": (0o177777, 0o4321),
    "x": (0o77777, 0),
    "xlow": (0o77777, 0),
    "y": (0o77777, 0),
    "out": (0o77777, 0),
    "cyr": (0o77777, 0),
}
OUTCOMES = {"match", "counterexample"}
MAX_VECTORS = 65536


@dataclass(frozen=True)
class Experiment:
    path: Path
    title: str
    origin: str
    scope: str
    expected: str
    axes: tuple[range | tuple[int, ...], ...]

    def vectors(self):
        return product(*self.axes)


def load_experiment(path: Path) -> Experiment:
    try:
        with path.open("rb") as stream:
            data = tomllib.load(stream)
        return parse_experiment(path, data)
    except (OSError, ValueError) as error:
        raise ValueError(f"{path}: {error}") from error


def parse_experiment(path: Path, data: dict) -> Experiment:
    for field in ("title", "origin", "scope", "expected"):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a nonempty string")
    expected = data["expected"]
    if expected not in OUTCOMES:
        raise ValueError(f"expected must be one of {', '.join(sorted(OUTCOMES))}")

    values = data.get("inputs", {})
    if not isinstance(values, dict):
        raise ValueError("inputs must be a TOML table")
    unknown = values.keys() - INPUTS.keys()
    if unknown:
        raise ValueError(f"unknown input names: {', '.join(sorted(unknown))}")

    axes = tuple(
        axis_for(name, values.get(name, [default]), limit)
        for name, (limit, default) in INPUTS.items()
    )
    if math.prod(map(len, axes)) > MAX_VECTORS:
        raise ValueError(f"the input grid exceeds {MAX_VECTORS} vectors")
    return Experiment(
        path, data["title"], data["origin"], data["scope"], expected, axes
    )


def axis_for(name: str, values, limit: int) -> range | tuple[int, ...]:
    if values == "all":
        return range(limit + 1)
    if (
        not isinstance(values, list)
        or not values
        or any(type(value) is not int or not 0 <= value <= limit for value in values)
    ):
        raise ValueError(
            f"{name} must be 'all' or a list of raw octal values up to {limit:o}"
        )
    if len(set(values)) != len(values):
        raise ValueError(f"{name} contains duplicate values")
    return tuple(values)
