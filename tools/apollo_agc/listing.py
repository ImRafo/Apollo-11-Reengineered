"""Extract Block II fixed-bank occupancy from plain-text yaYUL listings."""

import re
from pathlib import Path

from .memory import BANK_WORDS, FIXED_BANKS, Bank, fixed_address
from .source import read_text

HEADER = re.compile(
    r"^Apollo Guidance Computer \(AGC\) assembler, .*target AGC4\s*$", re.M
)
ROW = re.compile(r"^\d{6},\d{6}: ")
ADDRESS = re.compile(r"(?:[0-7]{2},|E[0-7],)?[0-7]{4}")
EXTENT = re.compile(r"Bank ([0-7]{2}):\s+([0-7]{4})/2000 words used\.")
CHECKSUM = re.compile(r"Bugger word [0-7]{5} at ([0-7]{2},[0-7]{4})\.")
WORD = re.compile(r"[0-7]{5}")
SUMMARY = ("Unresolved symbols", "Fatal errors", "Multiply-defined symbols")


def parse_listing(text: str) -> list[dict]:
    if not HEADER.search(text):
        raise ValueError("expected a plain-text yaYUL listing with target AGC4")
    for label in SUMMARY:
        count = re.findall(rf"^{label}:\s+(\d+)[ \t]*$", text, re.M)
        if len(count) != 1 or int(count[0]) != 0:
            raise ValueError(
                f"listing lacks a clean assembly summary for {label.lower()}"
            )

    emitted: list[set[int]] = [set() for _ in range(FIXED_BANKS)]
    extent: dict[int, int] = {}
    checksums: dict[int, int] = {}
    for number, line in enumerate(text.splitlines(), 1):
        if match := EXTENT.fullmatch(line):
            bank, size = (int(field, 8) for field in match.groups())
            if bank in extent or not 0 <= bank < FIXED_BANKS:
                raise ValueError(
                    f"line {number}: invalid or repeated fixed-bank usage row"
                )
            extent[bank] = size
        elif match := CHECKSUM.fullmatch(line):
            address = fixed_address(match[1])
            if address is None:
                raise ValueError(f"line {number}: checksum outside fixed memory")
            bank, offset = address
            if bank in checksums:
                raise ValueError(
                    f"line {number}: repeated checksum for bank {bank:02o}"
                )
            checksums[bank] = offset
        elif ROW.match(line):
            record_words(line, number, emitted)

    if len(extent) != FIXED_BANKS:
        raise ValueError(
            f"expected all {FIXED_BANKS} fixed-bank usage rows, found {len(extent)}"
        )
    return [
        Bank(bank, extent[bank], emitted[bank], checksums.get(bank)).report()
        for bank in range(FIXED_BANKS)
    ]


def record_words(line: str, number: int, emitted: list[set[int]]) -> None:
    # yaYUL prints the PC and label value in separate nine-character columns.
    raw_address = line[15:24].strip()
    if ADDRESS.fullmatch(raw_address) is None:
        return
    first, second = line[33:39].strip(), line[39:45].strip()
    if not first and not second:
        return
    if WORD.fullmatch(first) is None or (second and WORD.fullmatch(second) is None):
        raise ValueError(f"line {number}: invalid object word columns")
    address = fixed_address(raw_address)
    if address is None:
        return
    bank, offset = address
    end = offset + 1 + bool(second)
    if end > BANK_WORDS:
        raise ValueError(f"line {number}: object words cross a fixed-bank boundary")
    emitted[bank].update(range(offset, end))


def analyze_listing(path: Path) -> dict:
    try:
        banks = parse_listing(read_text(path))
    except ValueError as error:
        raise ValueError(f"{path}: {error}") from error
    return {"listing": str(path), "target": "AGC4", "banks": banks}


def format_listing(report: dict) -> str:
    lines = [f"{report['listing']} ({report['target']})"]
    for bank in report["banks"]:
        capacity, occupied = bank["capacity_words"], bank["occupied_words"]
        lines.append(
            f"Bank {bank['bank']}: {occupied}/{capacity} occupied ({occupied / capacity:.1%}), "
            f"assembler extent {bank['assembler_extent_words']}, "
            f"unlisted tail {bank['potentially_available_words']}"
        )
        for key, label in (
            ("occupied_ranges", "occupied"),
            ("unlisted_within_extent", "unlisted within extent"),
            ("unlisted_tail", "unlisted tail"),
        ):
            if bank[key]:
                lines.append(
                    f"  {label}: " + ", ".join("-".join(span) for span in bank[key])
                )
    return "\n".join(lines)
