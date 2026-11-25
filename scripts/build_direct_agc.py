"""Assemble the edited AGC sources directly from the local experiment branch."""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

if __package__:
    from .reproduce_luminary import assemble_staged, compare_ropes, read_rope
    from .virtualagc import REVISION, ROOT, TOOLS
else:
    from reproduce_luminary import assemble_staged, compare_ropes, read_rope
    from virtualagc import REVISION, ROOT, TOOLS

PROGRAMS = ("Luminary099", "Comanche055")


def build(program: str, tools: Path, output: Path, reference: Path | None) -> dict:
    metadata = json.loads((tools / "toolchain.json").read_text(encoding="utf-8"))
    if metadata.get("revision") != REVISION:
        raise ValueError(f"{tools}: expected Virtual AGC {REVISION}")
    proofed = read_rope(reference) if reference is not None else None
    working = output / "source"
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"{output}: use an empty output directory")
    working.mkdir(parents=True)
    for path in (ROOT / program).glob("*.agc"):
        shutil.copyfile(path, working / path.name)
    rope = assemble_staged(working, tools, output, filename=f"{program}.bin")
    report = {
        "program": program,
        "rope_bytes": len(rope),
        "sha256": hashlib.sha256(rope).hexdigest(),
        "virtual_agc_revision": REVISION,
    }
    if proofed is not None:
        report["comparison"] = compare_ropes(rope, proofed)
    (output / "build.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("program", choices=PROGRAMS)
    parser.add_argument("--toolchain", type=Path, default=TOOLS)
    parser.add_argument("--reference", type=Path, help="optional comparison rope")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or (ROOT / "build" / "direct-sources" / args.program)
    try:
        report = build(
            args.program, args.toolchain.resolve(), output.resolve(), args.reference
        )
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"AGC source build: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
