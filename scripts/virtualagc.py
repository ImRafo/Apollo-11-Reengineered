"""Fetch pinned Virtual AGC source and build the host tools used here."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIRTUAL_AGC_URL = "https://github.com/virtualagc/virtualagc.git"
REVISION = "27b7ae91f0a8f0e9145091dba12eb66d543c529a"
ZIG_VERSION = "0.15.2"
CHECKOUT = ROOT / "build" / "virtualagc"
TOOLS = ROOT / "build" / "historical-tools"
SOURCE_DIRS = ("yaYUL", "Tools", "Luminary099", "yaAGC")


def git(checkout: Path, *arguments: str) -> str:
    return subprocess.check_output(
        ["git", "-C", checkout, *arguments], text=True, encoding="utf-8"
    ).strip()


def prepare_checkout(checkout: Path) -> None:
    if not (checkout / ".git").exists():
        checkout.mkdir(parents=True, exist_ok=True)
        if any(checkout.iterdir()):
            raise ValueError(
                f"expected an empty destination or Virtual AGC checkout: {checkout}"
            )
        git(checkout, "init", "--quiet")
        git(checkout, "remote", "add", "origin", VIRTUAL_AGC_URL)
        git(checkout, "config", "remote.origin.promisor", "true")
        git(checkout, "config", "remote.origin.partialclonefilter", "blob:none")

    # A fetch or checkout interrupted before HEAD exists can be resumed.
    actual = subprocess.run(
        ["git", "-C", checkout, "rev-parse", "--verify", "--quiet", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if actual.returncode:
        if git(checkout, "remote", "get-url", "origin") != VIRTUAL_AGC_URL:
            raise ValueError(f"{checkout}: unexpected origin")
        git(checkout, "sparse-checkout", "set", *SOURCE_DIRS)
        git(checkout, "fetch", "--depth", "1", "--filter=blob:none", "origin", REVISION)
        git(checkout, "checkout", "--quiet", "--detach", "FETCH_HEAD")
    verify_checkout(checkout)


def verify_checkout(checkout: Path) -> None:
    if (
        not (checkout / ".git").exists()
        or git(checkout, "rev-parse", "HEAD") != REVISION
    ):
        raise ValueError(f"{checkout}: expected Virtual AGC at revision {REVISION}")
    metadata = git(checkout, "status", "--porcelain", "--untracked-files=all")
    if metadata:
        raise ValueError(f"{checkout}: expected a clean Virtual AGC checkout")
    for directory in SOURCE_DIRS:
        if not (checkout / directory).is_dir():
            raise ValueError(
                f"{checkout}: missing {directory}; include it in the sparse checkout"
            )


def tool_path(directory: Path, name: str) -> Path:
    return directory / (name + ".exe" if os.name == "nt" else name)


def compiler_command(cc: str | None) -> tuple[list[str], str]:
    if cc is not None:
        version = subprocess.check_output([cc, "--version"], text=True).splitlines()[0]
        return [cc], version
    zig = [sys.executable, "-m", "ziglang"]
    version = subprocess.check_output([*zig, "version"], text=True).strip()
    if version != ZIG_VERSION:
        raise ValueError(f"expected Zig {ZIG_VERSION}, got {version}")
    command = [*zig, "cc", "-Wno-error=date-time"]
    if os.name == "nt":
        command.extend(("-target", "x86_64-windows-gnu"))
    return command, f"Zig {version}"


def build_tools(checkout: Path, output: Path, cc: str | None) -> None:
    verify_checkout(checkout)
    command, compiler = compiler_command(cc)
    output.mkdir(parents=True, exist_ok=True)
    metadata = output / "toolchain.json"
    metadata.unlink(missing_ok=True)
    version_header = output / "version.h"
    version_header.write_text(f'#define NVER "{REVISION[:12]}"\n', encoding="ascii")
    common = [*command, "-O2", "-include", version_header]
    assembler = sorted((checkout / "yaYUL").glob("*.c"))
    subprocess.run(
        [*common, *assembler, "-o", tool_path(output, "yaYUL"), "-lm"], check=True
    )
    subprocess.run(
        [
            *common,
            "-DMAIN_PROGRAM",
            checkout / "Tools" / "oct2bin.c",
            checkout / "Tools" / "utils.c",
            "-o",
            tool_path(output, "oct2bin"),
        ],
        check=True,
    )
    metadata.write_text(
        json.dumps({"revision": REVISION, "compiler": compiler}, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, default=CHECKOUT)
    parser.add_argument("--output", type=Path, default=TOOLS)
    parser.add_argument(
        "--cc", help="path to a GCC-compatible compiler; default: pinned Zig"
    )
    args = parser.parse_args()
    try:
        checkout, output = args.checkout.resolve(), args.output.resolve()
        prepare_checkout(checkout)
        build_tools(checkout, output, args.cc)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"Virtual AGC toolchain: {error}", file=sys.stderr)
        return 1
    print(f"Built yaYUL and oct2bin for {REVISION} in {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
