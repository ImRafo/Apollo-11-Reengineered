"""Assemble Luminary 099 and compare the rope with its proofed octal reference."""

import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import sys
from collections import Counter
from pathlib import Path

if __package__:
    from .virtualagc import CHECKOUT, REVISION, ROOT, TOOLS, tool_path, verify_checkout
else:
    from virtualagc import CHECKOUT, REVISION, ROOT, TOOLS, tool_path, verify_checkout

REFERENCE_SHA256 = "1f5326e038de5b741b2f27b01ec949dbd688cf1906994e997402587c8628f40e"
WORDS_PER_BANK = 0o2000
BANK_ORDER = (2, 3, 0, 1, *range(4, 0o44))
ROPE_BYTES = len(BANK_ORDER) * WORDS_PER_BANK * 2
ALIASES = {
    "LAMBERT_AIMPOINT_GUIDANCE.agc": "GENERAL_LAMBERT_AIMPOINT_GUIDANCE.agc",
    "TRIM_GIMBAL_CNTROL_SYSTEM.agc": "TRIM_GIMBAL_CONTROL_SYSTEM.agc",
}


def read_rope(path: Path) -> bytes:
    data = path.read_bytes()
    if len(data) != ROPE_BYTES:
        raise ValueError(f"{path}: expected {ROPE_BYTES} bytes, found {len(data)}")
    return data


def compare_ropes(assembled: bytes, reference: bytes) -> dict:
    if len(assembled) != ROPE_BYTES or len(reference) != ROPE_BYTES:
        raise ValueError(f"both rope images must contain {ROPE_BYTES} bytes")
    differences = Counter()
    examples = []
    for index, ((actual,), (expected,)) in enumerate(
        zip(
            struct.iter_unpack(">H", assembled),
            struct.iter_unpack(">H", reference),
            strict=True,
        )
    ):
        if actual == expected:
            continue
        bank_index, offset = divmod(index, WORDS_PER_BANK)
        bank = f"{BANK_ORDER[bank_index]:02o}"
        differences[bank] += 1
        if len(examples) < 16:
            examples.append(
                {
                    "bank": bank,
                    "offset": f"{offset:04o}",
                    "assembled_encoded_word": f"{actual:06o}",
                    "reference_encoded_word": f"{expected:06o}",
                }
            )
    return {
        "byte_identical": not differences,
        "rope_bytes": ROPE_BYTES,
        "assembled_sha256": hashlib.sha256(assembled).hexdigest(),
        "reference_sha256": hashlib.sha256(reference).hexdigest(),
        "differing_encoded_words": sum(differences.values()),
        "differences_by_bank": dict(sorted(differences.items())),
        "first_differences": examples,
    }


def decode_reference(checkout: Path, tools: Path, output: Path) -> bytes:
    binsource = checkout / "Luminary099" / "Luminary099.binsource"
    log = output / "oct2bin.log"
    with binsource.open("rb") as stdin, log.open("wb") as diagnostics:
        result = subprocess.run(
            [tool_path(tools, "oct2bin")],
            cwd=output,
            stdin=stdin,
            stdout=diagnostics,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if result.returncode:
        raise ValueError(f"oct2bin failed with exit {result.returncode}; see {log}")
    reference = read_rope(output / "oct2bin.bin")
    if hashlib.sha256(reference).hexdigest() != REFERENCE_SHA256:
        raise ValueError(
            "decoded reference does not match the proofed reference SHA-256"
        )
    return reference


def assemble(checkout: Path, tools: Path, output: Path, source: str) -> bytes:
    working = output / "source"
    working.mkdir()
    program = (checkout if source == "upstream" else ROOT) / "Luminary099"
    for path in program.glob("*.agc"):
        shutil.copyfile(path, working / path.name)
    if source == "archive-aliases":
        for alias, original in ALIASES.items():
            shutil.copyfile(working / original, working / alias)

    listing, log = output / "assembly.lst", output / "assembly.log"
    with listing.open("wb") as stdout, log.open("wb") as stderr:
        result = subprocess.run(
            [tool_path(tools, "yaYUL"), "--unpound-page", "MAIN.agc"],
            cwd=working,
            stdout=stdout,
            stderr=stderr,
            check=False,
        )
    if result.returncode:
        raise ValueError(
            f"yaYUL failed with exit {result.returncode}; see {listing} and {log}"
        )
    binary = working / "MAIN.agc.bin"
    data = read_rope(binary)
    binary.replace(output / "Luminary099.bin")
    return data


def reproduce(checkout: Path, tools: Path, output: Path, source: str) -> dict:
    verify_checkout(checkout)
    metadata = json.loads((tools / "toolchain.json").read_text(encoding="utf-8"))
    if metadata.get("revision") != REVISION:
        raise ValueError(f"{tools}: toolchain is not marked as built from {REVISION}")
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError(f"{output}: use an empty output directory")
    reference = decode_reference(checkout, tools, output)
    assembled = assemble(checkout, tools, output, source)
    report = {
        "virtual_agc_revision": REVISION,
        "compiler": metadata["compiler"],
        "source": source,
        **compare_ropes(assembled, reference),
    }
    (output / "verification.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, default=CHECKOUT)
    parser.add_argument("--toolchain", type=Path, default=TOOLS)
    parser.add_argument("--output", type=Path, default=ROOT / "build" / "luminary099")
    parser.add_argument(
        "--source",
        choices=("upstream", "archive", "archive-aliases"),
        default="upstream",
    )
    args = parser.parse_args()
    try:
        report = reproduce(
            args.checkout.resolve(),
            args.toolchain.resolve(),
            args.output.resolve(),
            args.source,
        )
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"Luminary reproduction: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return int(not report["byte_identical"])


if __name__ == "__main__":
    raise SystemExit(main())
