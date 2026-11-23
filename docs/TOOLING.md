# AGC analysis tools

Install the project with `python -m pip install -e .` from its root.
The same CLI is available as `python -m apollo_agc`. Each command writes text
by default and accepts `--format json` for structured output.

## Source analysis

```sh
apollo-agc analyze Luminary099/MAIN.agc
apollo-agc analyze Luminary099 Comanche055 --format json
```

A directory selects its immediate `.agc` files. The analyzer counts physical
lines, comments, labels, directives, native instructions, interpretive
statements and include markers. Include contents are analyzed when supplied
as input files. The lexer recognizes column-one labels, early relative labels,
eight-column tabs and `#` comments. It accepts UTF-8 with an optional BOM and
CRLF or LF line endings. It treats the first recognized interpretive mnemonic
as the line's operation and retains the remaining tokens. Context-dependent
operand continuations use a column heuristic. Symbol resolution, operand
validation and timing require assembler or emulator evidence.

Malformed lines appear with line numbers in the report. Use `--strict` to
return exit status 1 when they occur. Unrecognized statements get their own
count. Read and decoding errors use exit status 1 with a path in the diagnostic.
Invalid command arguments use exit status 2.

## Source comparison

```sh
apollo-agc compare Luminary099/EXECUTIVE.agc Comanche055/EXECUTIVE.agc --format json
```

The report counts additions and removals by statement, preserving duplicates.
It compares the ordered instruction sequence as well as the placement of
directives and other statements. Spacing is normalized, and comment text is
reported independently. Paired interpretive mnemonics are represented as a
single source statement. Source comparison yields source-level evidence.

## Fixed-bank analysis

```sh
apollo-agc memory build/luminary099/assembly.lst --format json
```

Use the plain-text AGC4 listing from the [pinned assembler](HISTORICAL_BUILD.md).
The report requires a complete 36-bank table and a clean assembly summary.
Occupied words come from emitted object columns and checksum locations.
Offsets and range endpoints are octal and inclusive. Totals are decimal
counts. Erasable memory is outside this report's scope. Gaps inside the
assembler extent can include reservations. The unlisted tail is potentially
available and requires review before allocation.

## Optimization records

```sh
apollo-agc optimization optimizations/proposal.template.json
```

Schema version 1 accepts `proposed`, `measured`, `verified`, or `rejected`.
A measured metric records integer `original` and `modified` values and
an `evidence` reference. `execution_mct` uses memory-cycle timings for the
stated path. Test records use `not_run`, `pass`, or `fail`. The validator
checks structure and the presence of evidence references. Reviewers assess
the evidence itself.
