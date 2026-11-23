# Project architecture

The archival transcriptions are the primary historical inputs. Original host
tools live in the `apollo_agc` Python package. The command-line interface
dispatches to focused modules and renders the same result as text or JSON.

| Module | Responsibility |
| --- | --- |
| `source` | Decode UTF-8, classify physical lines, recognize symbols and mnemonics |
| `analysis` | Aggregate line categories, operation counts and diagnostics |
| `comparison` | Compare normalized statements and track ordered changes |
| `memory` | Model the Block II fixed address space and report occupied ranges |
| `listing` | Consume yaYUL listing columns and validate the assembly summary |
| `optimization` | Validate and render structured evidence records |

The tools run without a Python runtime dependency beyond the standard library.
Unit tests call the same parsing and reporting code as the installed CLI.
The host package contains the tools, while the Git repository contains the
historical archives and build scripts.

Historical reproduction uses a separate pinned Virtual AGC checkout. Scripts
build yaYUL and oct2bin, assemble a working copy, decode the proofed octal
reference and compare the byte streams. A bounded yaAGC harness exercises the
verified image. Build products and logs live under `build/`.

See [hardware constraints](AGC_CONSTRAINTS.md), [tool usage](TOOLING.md) and
[historical build evidence](HISTORICAL_BUILD.md).
