"""Compile a headless harness against the pinned yaAGC CPU core."""

import os
import subprocess
from pathlib import Path

if __package__:
    from .virtualagc import ROOT, compiler_command, tool_path, verify_checkout
else:
    from virtualagc import ROOT, compiler_command, tool_path, verify_checkout


def build_harness(checkout: Path, output: Path, name: str, cc: str | None) -> Path:
    verify_checkout(checkout)
    command, _ = compiler_command(cc)
    source = checkout / "yaAGC"
    components = ["agc_engine.c", "agc_engine_init.c", "NullAPI.c", "rfopen.c"]
    if os.name == "nt":
        components.append("random.c")

    output.mkdir(parents=True, exist_ok=True)
    harness = tool_path(output, name)
    subprocess.run(
        [
            *command,
            "-O2",
            "-I",
            source,
            ROOT / "scripts" / f"{name}.c",
            ROOT / "scripts" / "headless_io.c",
            *(source / component for component in components),
            "-o",
            harness,
        ],
        check=True,
    )
    return harness
