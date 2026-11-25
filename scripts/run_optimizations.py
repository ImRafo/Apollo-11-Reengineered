"""Assemble and compare baseline and candidate AGC fragments in yaAGC."""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

if __package__:
    from .optimization_assembly import ENTRY, STOP, assemble_fragment
    from .optimization_cases import Experiment, load_experiment
    from .optimization_probe import compare, encode_inputs, measure
    from .virtualagc import CHECKOUT, REVISION, ROOT, TOOLS, tool_path
    from .yaagc import build_harness
else:
    from optimization_assembly import ENTRY, STOP, assemble_fragment
    from optimization_cases import Experiment, load_experiment
    from optimization_probe import compare, encode_inputs, measure
    from virtualagc import CHECKOUT, REVISION, ROOT, TOOLS, tool_path
    from yaagc import build_harness

EXPERIMENTS = ROOT / "experiments" / "assembly"


def optional_data(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def run_experiment(
    experiment: Experiment, assembler: Path, harness: Path, output: Path
) -> dict:
    folder = experiment.path.parent
    inputs = encode_inputs(experiment)
    shared = optional_data(folder / "data.agc")
    measurements = {}
    words = {}
    for variant in ("baseline", "candidate"):
        body = (folder / f"{variant}.agc").read_text(encoding="utf-8")
        constants = shared + "\n" + optional_data(folder / f"{variant}-data.agc")
        fragment = assemble_fragment(assembler, output / variant, body, constants)
        measurements[variant] = measure(harness, fragment.rope, ENTRY, STOP, inputs)
        words[variant] = {"code": fragment.code_words, "data": fragment.data_words}
    report = {
        "title": experiment.title,
        "origin": experiment.origin,
        "scope": experiment.scope,
        "virtual_agc_revision": REVISION,
        "expected": experiment.expected,
        "words": words,
        **compare(experiment, measurements["baseline"], measurements["candidate"]),
    }
    (output / "comparison.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "manifests",
        nargs="*",
        type=Path,
        help="experiment.toml files; default: run all",
    )
    parser.add_argument("--checkout", type=Path, default=CHECKOUT)
    parser.add_argument("--toolchain", type=Path, default=TOOLS)
    parser.add_argument("--output", type=Path, default=ROOT / "build" / "optimizations")
    parser.add_argument(
        "--cc", help="path to a GCC-compatible compiler; default: pinned Zig"
    )
    args = parser.parse_args()

    manifests = args.manifests or sorted(EXPERIMENTS.glob("*/experiment.toml"))
    output = args.output.resolve() / f"run-{uuid4().hex[:12]}"
    try:
        if not manifests:
            raise ValueError("supply at least one experiment manifest")
        experiments = [load_experiment(path.resolve()) for path in manifests]
        tools = args.toolchain.resolve()
        metadata = json.loads((tools / "toolchain.json").read_text(encoding="utf-8"))
        if metadata.get("revision") != REVISION:
            raise ValueError(
                f"{tools}: expected tools built from Virtual AGC {REVISION}"
            )
        harness = build_harness(args.checkout.resolve(), output, "agc_probe", args.cc)
        assembler = tool_path(tools, "yaYUL")

        failures = []
        for number, experiment in enumerate(experiments, 1):
            name = experiment.path.parent.name
            report = run_experiment(
                experiment, assembler, harness, output / f"{number:02d}-{name}"
            )
            if not report["matches_expectation"]:
                failures.append(name)
            baseline, candidate = (
                report["words"]["baseline"],
                report["words"]["candidate"],
            )
            print(
                f"{name}: {report['outcome']}, {report['differing_vectors']}/{report['vectors']} "
                f"vectors differ, code {baseline['code']} -> {candidate['code']}, "
                f"data {baseline['data']} -> {candidate['data']}, "
                f"MCT saved {report['mct_saved_histogram']}"
            )
        print(f"Reports written to {output}")
        if failures:
            print(
                f"Unexpected experimental outcomes: {', '.join(failures)}",
                file=sys.stderr,
            )
        return int(bool(failures))
    except (
        OSError,
        ValueError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
    ) as error:
        print(f"AGC experiment: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
