"""Fixed-memory addresses and bank accounting for the Block II AGC."""

from dataclasses import dataclass, field

BANK_WORDS = 0o2000
FIXED_BANKS = 0o44


def fixed_address(raw: str) -> tuple[int, int] | None:
    """Return physical fixed bank and word offset, or None for erasable memory."""
    if raw.startswith("E"):
        return None
    bank, separator, address = raw.partition(",")
    if separator:
        number, sreg = int(bank, 8), int(address, 8)
        if not 0 <= number < FIXED_BANKS or not 0o2000 <= sreg < 0o4000:
            raise ValueError(f"invalid banked fixed address {raw}")
        return number, sreg - 0o2000
    sreg = int(raw, 8)
    if 0 <= sreg < 0o2000:
        return None
    if 0o4000 <= sreg <= 0o7777:
        return divmod(sreg, BANK_WORDS)
    raise ValueError(f"ambiguous or invalid fixed address {raw}")


def ranges(offsets: set[int]) -> list[list[str]]:
    """Coalesce inclusive ranges expressed as octal bank-relative offsets."""
    result = []
    start = end = None
    for offset in sorted(offsets):
        if start is None:
            start = end = offset
        elif offset == end + 1:
            end = offset
        else:
            result.append([f"{start:04o}", f"{end:04o}"])
            start = end = offset
    if start is not None:
        result.append([f"{start:04o}", f"{end:04o}"])
    return result


@dataclass
class Bank:
    number: int
    high_water_mark: int
    words: set[int] = field(default_factory=set)
    checksum: int | None = None

    def report(self) -> dict:
        if not 0 <= self.number < FIXED_BANKS:
            raise ValueError(f"invalid Block II fixed bank {self.number:02o}")
        if not 0 <= self.high_water_mark <= BANK_WORDS:
            raise ValueError(f"invalid high-water mark in bank {self.number:02o}")
        if any(not 0 <= offset < self.high_water_mark for offset in self.words):
            raise ValueError(
                f"emitted words outside the reported extent in bank {self.number:02o}"
            )
        occupied = self.words.copy()
        if self.checksum is not None:
            if not 0 <= self.checksum < BANK_WORDS or self.checksum in occupied:
                raise ValueError(
                    f"invalid checksum placement in bank {self.number:02o}"
                )
            occupied.add(self.checksum)
        inside = set(range(self.high_water_mark)) - occupied
        tail = set(range(self.high_water_mark, BANK_WORDS)) - occupied
        return {
            "bank": f"{self.number:02o}",
            "capacity_words": BANK_WORDS,
            "assembler_extent_words": self.high_water_mark,
            "emitted_words": len(self.words),
            "occupied_words": len(occupied),
            "potentially_available_words": len(tail),
            "checksum_offset": None
            if self.checksum is None
            else f"{self.checksum:04o}",
            "occupied_ranges": ranges(occupied),
            "unlisted_within_extent": ranges(inside),
            "unlisted_tail": ranges(tail),
        }
