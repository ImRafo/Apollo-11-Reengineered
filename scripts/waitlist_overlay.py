"""Build the size-preserving WAITLIST alternative in a staged Luminary rope."""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

if __package__:
    from .optimization_cases import parse_experiment
    from .optimization_probe import compare, encode_inputs, measure
    from .reproduce_luminary import (
        assemble_staged,
        compare_ropes,
        decode_reference,
        stage_program,
    )
    from .virtualagc import CHECKOUT, REVISION, ROOT, TOOLS, verify_checkout
    from .yaagc import build_harness
else:
    from optimization_cases import parse_experiment
    from optimization_probe import compare, encode_inputs, measure
    from reproduce_luminary import (
        assemble_staged,
        compare_ropes,
        decode_reference,
        stage_program,
    )
    from virtualagc import CHECKOUT, REVISION, ROOT, TOOLS, verify_checkout
    from yaagc import build_harness

REPLACEMENT = (
    ROOT / "experiments" / "assembly" / "waitlist-direct-ccs" / "flight-overlay.agc"
)
ORIGINAL = (
    (b"CA", b"LONGTIME"),
    (b"CCS", b"A"),
    (b"TCF", b"LONGCYCL"),
    (b"TCF", b"+2"),
    (b"TCF", b"LONGPOOH"),
)
FIXED_BANK = 0o01
ENTRY = 0o3456
CHECKSUM_OFFSET = 0o1777
LONGTIME = 0o1153
DISPATCH_PATHS = (
    ("positive", range(1, 0o40000), 0o3466, 2),
    ("positive_zero", (0,), 0o3463, 2),
    ("negative", range(0o40000, 0o77777), 0o3521, 2),
    ("negative_zero", (0o77777,), 0o3463, 1),
)


def replace_dispatch(text: bytes, replacement: bytes) -> bytes:
    lines = text.splitlines(keepends=True)
    statements = [tuple(line.partition(b"#")[0].split()) for line in lines]
    length = len(ORIGINAL)
    starts = [
        i
        for i in range(len(lines) - length + 1)
        if tuple(statements[i : i + length]) == ORIGINAL
    ]
    if len(starts) != 1:
        raise ValueError("expected one unchanged WAITLIST dispatch block")

    new_lines = replacement.splitlines()
    if len(new_lines) != length or any(
        not line.partition(b"#")[0].strip() for line in new_lines
    ):
        raise ValueError(
            "the staged WAITLIST edit must retain its five instruction rows"
        )
    start = starts[0]
    newline = b"\r\n" if lines[start].endswith(b"\r\n") else b"\n"
    lines[start : start + length] = [line + newline for line in new_lines]
    return b"".join(lines)


def build_overlay(checkout: Path, tools: Path, output: Path) -> dict:
    verify_checkout(checkout)
    metadata = json.loads((tools / "toolchain.json").read_text(encoding="utf-8"))
    if metadata.get("revision") != REVISION:
        raise ValueError(f"{tools}: expected tools built from Virtual AGC {REVISION}")

    output.mkdir(parents=True)
    reference = decode_reference(checkout, tools, output)
    staged = stage_program(checkout, output, "upstream")
    path = staged / "WAITLIST.agc"
    path.write_bytes(replace_dispatch(path.read_bytes(), REPLACEMENT.read_bytes()))
    variant = assemble_staged(staged, tools, output)
    comparison = compare_ropes(variant, reference)

    code_offsets = range(ENTRY - 0o2000, ENTRY - 0o2000 + len(ORIGINAL))
    allowed = {
        (f"{FIXED_BANK:02o}", f"{offset:04o}")
        for offset in (*code_offsets, CHECKSUM_OFFSET)
    }
    actual = {
        (word["bank"], word["offset"]) for word in comparison["first_differences"]
    }
    if actual != allowed or comparison["differing_encoded_words"] != len(allowed):
        raise ValueError(f"unexpected WAITLIST rope differences: {sorted(actual)}")

    return {
        "virtual_agc_revision": REVISION,
        "bank": f"{FIXED_BANK:02o}",
        "entry": f"{ENTRY:04o}",
        "dispatch_words": len(ORIGINAL),
        **comparison,
    }


def profile_dispatch(harness: Path, reference: Path, variant: Path) -> dict:
    paths = {}
    for name, values, stop, expected_savings in DISPATCH_PATHS:
        experiment = parse_experiment(
            REPLACEMENT,
            {
                "title": name,
                "origin": "Luminary099 WAITLIST, bank 01",
                "scope": "High-word dispatch through its first destination",
                "expected": "match",
                "inputs": {"x": list(values)},
            },
        )
        inputs = encode_inputs(experiment)
        before = measure(
            harness, reference, ENTRY, stop, inputs, bank_and_x=(FIXED_BANK, LONGTIME)
        )
        after = measure(
            harness, variant, ENTRY, stop, inputs, bank_and_x=(FIXED_BANK, LONGTIME)
        )
        summary = compare(experiment, before, after)
        paths[name] = {
            "destination": f"{stop:04o}",
            "matches_timing": summary["mct_saved_histogram"]
            == {expected_savings: len(values)},
            **summary,
        }
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, default=CHECKOUT)
    parser.add_argument("--toolchain", type=Path, default=TOOLS)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "build" / "waitlist-experiment"
    )
    parser.add_argument(
        "--cc", help="path to a GCC-compatible compiler; default: pinned Zig"
    )
    args = parser.parse_args()
    output = args.output.resolve() / f"run-{uuid4().hex[:12]}"
    try:
        checkout = args.checkout.resolve()
        report = build_overlay(checkout, args.toolchain.resolve(), output)
        harness = build_harness(checkout, output, "agc_probe", args.cc)
        paths = profile_dispatch(
            harness, output / "oct2bin.bin", output / "Luminary099.bin"
        )
        report["longtime_address"] = f"{LONGTIME:04o}"
        report["dispatch_paths"] = paths
        (output / "overlay.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
    except (
        OSError,
        ValueError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
    ) as error:
        print(f"WAITLIST overlay: {error}", file=sys.stderr)
        return 1
    print(
        f"WAITLIST overlay: five code words and one checksum changed in bank {report['bank']}"
    )
    for name, summary in paths.items():
        print(
            f"  {name}: {summary['vectors']} vectors, MCT saved {summary['mct_saved_histogram']}"
        )
    print(f"Report and rope written to {output}")
    return int(
        not all(
            path["matches_expectation"] and path["matches_timing"]
            for path in paths.values()
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
