"""Assemble fixed-fixed AGC fragments and measure their emitted word counts."""

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

if __package__:
    from .reproduce_luminary import read_rope
else:
    from reproduce_luminary import read_rope

ENTRY = 0o4000
DATA = 0o4400
STOP = 0o4600
SYMBOLS = """X               EQUALS  100
XLOW            EQUALS  101
Y               EQUALS  102
OUT             EQUALS  103"""
ADDRESS_ROW = re.compile(r"^\d{6},\d{6}: +([0-7]{4})\b")
FENCES = {"BENCHEND", "ENDDATA"}


@dataclass(frozen=True)
class Fragment:
    rope: Path
    code_words: int
    data_words: int


def source(body: str, constants: str) -> str:
    return (
        f"{SYMBOLS}\n"
        f"                SETLOC  {ENTRY:o}\n"
        f"{body.rstrip()}\n"
        "BENCHEND        TCF     BENCHSTP\n"
        f"                SETLOC  {DATA:o}\n"
        f"{constants.rstrip()}\n"
        "ENDDATA         OCT     00000\n"
        f"                SETLOC  {STOP:o}\n"
        "BENCHSTP        TCF     BENCHSTP\n"
    )


def measure_words(listing: str) -> tuple[int, int]:
    fences = {}
    for line in listing.splitlines():
        address = ADDRESS_ROW.match(line)
        fields = line[45:].split(maxsplit=1)
        if address is not None and fields and fields[0] in FENCES:
            symbol = fields[0]
            if symbol in fences:
                raise ValueError(f"ambiguous yaYUL listing fence {symbol}")
            fences[symbol] = int(address[1], 8)
    if fences.keys() != FENCES:
        raise ValueError("yaYUL listing is missing the experiment fences")
    end, data_end = fences["BENCHEND"], fences["ENDDATA"]
    if not (ENTRY < end < DATA <= data_end < STOP):
        raise ValueError("experiment fragment exceeded its fixed-fixed allocation")
    return end - ENTRY, data_end - DATA


def assemble_fragment(
    assembler: Path, output: Path, body: str, constants: str
) -> Fragment:
    output.mkdir(parents=True)
    (output / "MAIN.agc").write_text(
        source(body, constants), encoding="utf-8", newline="\n"
    )
    listing, diagnostic = output / "assembly.lst", output / "assembly.log"
    with listing.open("wb") as stdout, diagnostic.open("wb") as stderr:
        result = subprocess.run(
            [assembler, "MAIN.agc"],
            cwd=output,
            stdout=stdout,
            stderr=stderr,
            check=False,
            timeout=30,
        )
    if result.returncode:
        raise ValueError(
            f"yaYUL failed with exit {result.returncode}; see {listing} and {diagnostic}"
        )
    rope = output / "MAIN.agc.bin"
    read_rope(rope)
    code_words, data_words = measure_words(listing.read_text(encoding="utf-8"))
    return Fragment(rope, code_words, data_words)
