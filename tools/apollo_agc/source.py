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
    ABS ABVAL ACOS ARCCOS ARCSIN ASIN AXC,1 AXC,2 AXT,1 AXT,2 BDDV BDDV* BDSU BDSU*
    BHIZ BMN BOF BOFCLR BOFF BOFINV BOFSET BON BONCLR BONINV BONSET BOV BOVB BPL BVSU
    BVSU* BZE CALL CALRB CCALL CCALL* CGOTO CGOTO* CLEAR CLR CLRGO COS COSINE DAD DAD*
    DCOMP DDV DDV* DLOAD DLOAD* DMP DMP* DMPR DMPR* DOT DOT* DSQ DSU DSU* EXIT GOTO
    INCR,1 INCR,2 INVERT INVGO ITA ITCQ LXA,1 LXA,2 LXC,1 LXC,2 MXV MXV* NORM NORM*
    PDDL PDDL* PDVL PDVL* PUSH ROUND RTB RVQ SET SETGO SETPD SIGN SIGN* SIN SINE SL SL*
    SL1 SL1R SL2 SL2R SL3 SL3R SL4 SL4R SLOAD SLOAD* SLR SLR* SQRT SR SR* SR1 SR1R SR2
    SR2R SR3 SR3R SR4 SR4R SRR SRR* SSP SSP* STADR STCALL STODL STODL* STORE STOVL
    STOVL* STQ SXA,1 SXA,2 TAD TAD* TIX,1 TIX,2 TLOAD TLOAD* UNIT V/SC V/SC* VAD VAD*
    VCOMP VDEF VLOAD VLOAD* VPROJ VPROJ* VSL VSL* VSL1 VSL2 VSL3 VSL4 VSL5 VSL6 VSL7
    VSL8 VSQ VSR VSR* VSR1 VSR2 VSR3 VSR4 VSR5 VSR6 VSR7 VSR8 VSU VSU* VXM VXM*
    VXSC VXSC* VXV VXV* XAD,1 XAD,2 XCHX,1 XCHX,2 XSU,1 XSU,2
    """.split()
)

TOKEN = re.compile(r"[^ \t]+")
LABEL = re.compile(r"[A-Za-z0-9._/+*(),=\-]+")
OFFSET = re.compile(r"[+-][0-9]+D?")
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
    relative_label: str | None = None


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
    relative_label = None
    if first.start() == 0:
        label = first.group()
        if LABEL.fullmatch(label) is None:
            return SourceLine(
                number, "malformed", comment=comment, issue="invalid label"
            )
        tokens = tokens[1:]
    elif first.start() < 8 and OFFSET.fullmatch(first.group()):
        relative_label = first.group()
        if len(tokens) == 1:
            return SourceLine(
                number, "continuation", operands=(relative_label,), comment=comment
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
    elif operation in INTERPRETIVE:
        kind = "interpretive"
    elif not operands and tokens[0].start() >= 24 and LABEL.fullmatch(operation):
        return SourceLine(
            number,
            "continuation",
            label,
            operands=(operation,),
            comment=comment,
            relative_label=relative_label,
        )
    else:
        kind = "unrecognized"
    return SourceLine(
        number, kind, label, operation, operands, comment, relative_label=relative_label
    )
