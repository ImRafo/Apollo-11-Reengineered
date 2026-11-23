"""Run a bounded, headless yaAGC boot check on the verified Luminary rope."""

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path

if __package__:
    from .reproduce_luminary import REFERENCE_SHA256, read_rope
    from .virtualagc import CHECKOUT, ROOT, compiler_command, tool_path, verify_checkout
else:
    from reproduce_luminary import REFERENCE_SHA256, read_rope
    from virtualagc import CHECKOUT, ROOT, compiler_command, tool_path, verify_checkout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, default=CHECKOUT)
    parser.add_argument("--output", type=Path, default=ROOT / "build" / "emulator")
    parser.add_argument(
        "--cc", help="path to a GCC-compatible compiler; default: pinned Zig"
    )
    parser.add_argument("rope", type=Path)
    args = parser.parse_args()
    try:
        rope = args.rope.resolve()
        if hashlib.sha256(read_rope(rope)).hexdigest() != REFERENCE_SHA256:
            raise ValueError(
                "the boot check requires the byte-identical Luminary 099 rope"
            )
        checkout, output = args.checkout.resolve(), args.output.resolve()
        verify_checkout(checkout)
        command, _ = compiler_command(args.cc)

        output.mkdir(parents=True, exist_ok=True)
        source = checkout / "yaAGC"
        harness = tool_path(output, "luminary_smoke")
        components = ["agc_engine.c", "agc_engine_init.c", "NullAPI.c", "rfopen.c"]
        if os.name == "nt":
            components.append("random.c")
        subprocess.run(
            [
                *command,
                "-O2",
                "-I",
                source,
                ROOT / "scripts" / "luminary_smoke.c",
                *(source / component for component in components),
                "-o",
                harness,
            ],
            check=True,
        )
        result = subprocess.run(
            [harness, rope],
            cwd=output,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        (output / "smoke.json").write_text(result.stdout, encoding="utf-8")
        print(result.stdout.strip())
    except subprocess.CalledProcessError as error:
        if error.stderr:
            print(error.stderr.rstrip(), file=sys.stderr)
        print(f"yaAGC smoke check: {error}", file=sys.stderr)
        return 1
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(f"yaAGC smoke check: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
