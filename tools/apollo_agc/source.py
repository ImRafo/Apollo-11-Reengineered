"""Lexical analysis for the Block II yaYUL source format."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# Mnemonics from the Virtual AGC Block II manual and yaYUL AGC4 tables.
INSTRUCTIONS = frozenset(
    """
    -CCS AD ADS AUG BZF BZMF CA CAE CAF CCS COM CS DAS DCA DCOM DCS DDOUBL
    DIM DOUBLE DTCB DTCF DV DXCH EDRUPT EXTEND INCR INDEX INHINT LXCH MASK
    MP MSK MSU NDX OVSK QXCH RAND READ RELINT RESUME RETURN ROR RXOR SQUARE
    SU TC TCAA TCF TCR TS WAND WOR WRITE XCH XLQ XXALQ ZL ZQ
    """.split()
)
DIRECTIVES = frozenset(
    """
    -1DNADR -2CADR -2DNADR -3DNADR -4DNADR -5DNADR -6DNADR -DNCHAN -DNPTR
    -GENADR = =ECADR =MINUS 1DNADR 2BCADR 2CADR 2DEC 2DEC* 2DNADR 2FCADR 2OCT
    3DNADR 4DNADR 5DNADR 6DNADR ADRES BANK BBCON BBCON* BLOCK BNKSUM CADR
    CHECK= COUNT COUNT* DEC DEC* DNCHAN DNPTR EBANK= ECADR EQUALS ERASE FCADR
    GENADR MEMORY MM NV OCT OCTAL REMADR SBANK= SECSIZ SETLOC SUBRO VN
    """.split()
)
INTERPRETIVE = frozenset(
    """
    ABS ACOS ASIN AXC AXC,1 AXC,2 AX TSL BHIZ BINV BMN BOFF BOFSET BOFCLR
    BON BONCLR BONSET BOV BOVB BPL BZE CALL CALRB CCALL CLEAR CLRGO COS DAD
    DCALL DCOMP DDV DLOAD DMP DMPR DOT DROUND DSQ DSU EXIT GOTO INCR,1
    INCR,2 INTLOP INVGO ITA ITC ITCQ IX,1 IX,2 LXA LXA,1 LXA,2 LXC
    LXC,1 LXC,2 MXV NORM PDDL PDVL PUSH RTB RVQ SET SETGO SIGN SIN SL
    SL1 SL2 SL3 SL4 SLOAD SLR SL1R SL2R SL3R SL4R SQRT SR SR1 SR2 SR3 SR4
    SSP STADR STCALL STODL STODL* STORE STOVL STOVL* SWAP TAD TLOAD
    UNIT V/SC VAD VCOMP VDEF VLOAD VPROJ VSQ VSL VSL1 VSL2 VSR VSR1 VSR2
    VSUB VSU VXM VXSC VXSU XAD,1 XAD,2 XCHX XSU,1 XSU,2
    """.split()
)

TOKEN = re.compile(r"[^ \t]+")
LABEL = re.compile(r"[A-Za-z0-9._/+*(),=\-]+")
OFFSET = re.compile(r"[+-][0-9]+")
CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


@dataclass(frozen=True)
class SourceLine:
    number: int
    kind: str
    label: str | None = None
    operation: str | None = None
    operands: tuple[str, ...] = ()
    comment: str | None = None
    issue: str | None = None


def read_text(path: Path) -> str:
    """Read UTF-8 (optionally with BOM) and retain a path in failure messages."""
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValueError(f"{path}: invalid UTF-8 at byte {error.start}") from error
    except OSError as error:
        raise ValueError(f"{path}: {error.strerror or error}") from error


def parse_source(text: str) -> list[SourceLine]:
    """Read physical lines without resolving symbols or following include directives."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.removesuffix("\n").split("\n") if text else []
    return [parse_line(number, line) for number, line in enumerate(lines, 1)]


def parse_line(number: int, line: str) -> SourceLine:
    code, separator, comment_text = line.partition("#")
    comment = comment_text.strip() if separator else None
    if CONTROL.search(line):
        return SourceLine(
            number, "malformed", comment=comment, issue="control character"
        )

    code = code.expandtabs(8)
    tokens = list(TOKEN.finditer(code))
    if not tokens:
        return SourceLine(number, "comment" if separator else "blank", comment=comment)
    if code.startswith("$"):
        include = code[1:].strip()
        if not include or len(include.split()) != 1:
            return SourceLine(
                number, "malformed", comment=comment, issue="invalid include"
            )
        return SourceLine(number, "include", operands=(include,), comment=comment)

    first = tokens[0]
    label = None
    if first.start() == 0:
        label = first.group()
        if LABEL.fullmatch(label) is None:
            return SourceLine(
                number, "malformed", comment=comment, issue="invalid label"
            )
        tokens = tokens[1:]
    elif first.start() < 8 and OFFSET.fullmatch(first.group()):
        if len(tokens) == 1:
            return SourceLine(
                number, "continuation", operands=(first.group(),), comment=comment
            )
        tokens = tokens[1:]

    if not tokens:
        return SourceLine(number, "label", label=label, comment=comment)

    operation = tokens[0].group()
    operands = tuple(token.group() for token in tokens[1:])
    if operation in INSTRUCTIONS:
        kind = "instruction"
    elif operation in DIRECTIVES:
        kind = "directive"
    elif operation in INTERPRETIVE or operation.removesuffix("*") in INTERPRETIVE:
        kind = "interpretive"
    elif not operands and tokens[0].start() >= 16 and LABEL.fullmatch(operation):
        return SourceLine(
            number, "continuation", label, operands=(operation,), comment=comment
        )
    else:
        kind = "unrecognized"
    return SourceLine(number, kind, label, operation, operands, comment)
