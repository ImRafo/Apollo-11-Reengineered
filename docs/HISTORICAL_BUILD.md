# Reproducing Luminary 099

The default build uses Luminary 099/1 source from Virtual AGC revision
[`27b7ae91f0a8f0e9145091dba12eb66d543c529a`](https://github.com/virtualagc/virtualagc/tree/27b7ae91f0a8f0e9145091dba12eb66d543c529a).
The comparison baseline is the same revision's independently proofed octal
[`Luminary099.binsource`](https://github.com/virtualagc/virtualagc/blob/27b7ae91f0a8f0e9145091dba12eb66d543c529a/Luminary099/Luminary099.binsource).
Virtual AGC checked the octal values and memory-bank checksums against historical
listing scans. [Virtual AGC proofing notes](https://www.ibiblio.org/apollo/Luminary.html#ValidLuminary099).

## Build and verify

Install Python 3.11 or later and Git. The default compiler is Zig 0.15.2,
including the Windows x86-64 GNU target. On a POSIX host with a GCC-compatible
compiler, pass `--cc cc` to the toolchain and emulator commands.

```sh
python -m pip install ziglang==0.15.2
python scripts/virtualagc.py
python scripts/reproduce_luminary.py
python scripts/emulator_smoke.py build/luminary099/Luminary099.bin
```

The first command that runs a project script downloads a sparse checkout
into `build/virtualagc/` and compiles yaYUL and oct2bin into
`build/historical-tools/`. Use `--checkout PATH` to reuse a clean local
Virtual AGC checkout at the pinned revision. To run a second reproduction,
pass a fresh `--output PATH`.

The reproduction command copies the selected source to a working directory,
runs yaYUL and decodes the octal reference with oct2bin. It produces
`Luminary099.bin`, `assembly.lst`, `assembly.log`, and `verification.json`.
A reference digest mismatch, assembler error, or byte difference causes a
nonzero exit. Object differences count big-endian encoded words, including
any representation-bit changes. The dump stores banks in the order 02, 03,
00, 01, then 04 through 43 in octal.

## Verified observations

| Check | Result on Windows x86-64 with Zig 0.15.2 |
| --- | --- |
| Assembler | 0 fatal errors, 0 unresolved symbols, 1 erasable-bank warning |
| Rope size | 73,728 bytes |
| Byte comparison | 0 differing encoded words |
| Staged archive with aliases and relative-label layout corrected | 0 differing encoded words |
| SHA-256 | `1f5326e038de5b741b2f27b01ec949dbd688cf1906994e997402587c8628f40e` |
| Fixed-bank listing | 36 checksums and 36,575 emitted or checksum words |
| Headless yaAGC check | 4,096 cycles, Z from `4000` to `6521` octal |

The warning comes from `ERASABLE_ASSIGNMENTS.agc:1001` in the pinned
Virtual AGC source. The emulator check uses the CPU core and NullAPI with
zeroed erasable startup state and no spacecraft peripherals. It checks a
single deterministic boot checkpoint.

For the raw archive, alias-only build and verified normalized build, see the
[archive reproduction experiment](../experiments/archive-include-aliases.md).
Comanche 055 remains an archival and source-analysis input.
