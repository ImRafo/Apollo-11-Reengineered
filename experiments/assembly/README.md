# AGC assembly experiments

Each directory contains the original instruction sequence, a candidate, and
an input grid. The manifest links the sequence to the historical file and
describes which symbols and paths the fragment models. The staged WAITLIST
experiment also assembles and runs a complete Luminary 099 rope.

## Run the experiments

Set up the pinned Virtual AGC tools using the
[historical build guide](../../docs/HISTORICAL_BUILD.md).

```sh
python scripts/run_optimizations.py
python scripts/run_optimizations.py experiments/assembly/landing-negative-zero/experiment.toml
python scripts/waitlist_overlay.py
```

On a system with a GCC-compatible compiler, pass `--cc cc` to these
commands and to the historical toolchain setup. Runs save the assembled
inputs, diagnostics, and JSON reports under `build/`. The commands return
an error on an unexpected outcome. A documented counterexample is a
successful experiment.

## Fragment results

Code and data counts come from the assembler listing. Counts include
the modeled branches and any constants supplied for the fragment. A
positive MCT saving means the candidate arrived sooner at the common
checkpoint. Timing includes the shared jump to the checkpoint.

| Experiment | State differences | Code words | Data words | MCT saved |
| --- | ---: | ---: | ---: | --- |
| [Compact WAITLIST dispatch](waitlist-direct-ccs/) | 0 / 32,768 | 10 → 9 | 0 → 0 | 2 on every vector |
| [AOS pair with DCA](aos-nonadjacent-pair/) | 9 / 12 | 3 → 2 | 0 → 0 | 2 |
| [L cancellation with positive zero](landing-cancel-l/) | 32,768 / 32,768 | 2 → 1 | 1 → 1 | 2 |
| [L cancellation with negative zero](landing-negative-zero/) | 0 / 32,768 | 2 → 1 | 1 → 1 | 2 |
| [Direct load in Comanche P11](p11-direct-one/) | 0 / 12 | 2 → 1 | 2 → 2 | 2 |
| [Doubled half as a stored word](cm-half-overflow/) | 6 / 6 | 2 → 1 | 1 → 2 | 2 |
| [IMU paired fixed load](imu-fixed-pair/) | 0 / 18 | 3 → 2 | 2 → 4 | 2 |
| [Remove the Comanche roll store](cm-roll-store-entry/) | 3 / 12 | 8 → 7 | 0 → 0 | 2 |
| [Remove the P52 repeat load](p52-reload-entry/) | 6 / 8 | 12 → 11 | 2 → 2 | 2 |
| [Comanche sign branch](comanche-sign-branch/) | 0 / 32,768 | 8 → 8 | 2 → 2 | 2 on 16,384 vectors |
| [Self-check using SU](selfcheck-subtract/) | 0 / 36 | 2 → 3 | 0 → 0 | −1 |

The AOS pair fails because the low word of AOSQ lies between AOSQ and AOSR.
The doubled-half example loses positive overflow when an octal `40000`
word is loaded as a 15-bit signed value. The removed stores and loads in
Comanche and P52 also have alternate entry paths. These differences are
recorded with raw octal state in the generated reports.

## WAITLIST in two complete ropes

The [Assembly replacement](waitlist-direct-ccs/flight-overlay.agc) fits the
original five words at `01,3456–3462` octal. The rope comparison also found
one updated bank checksum at `01,3777`. The original and staged ropes were
executed from the same program counter with `LONGTIME` at its historical
erasable address `1153`.

| High word | Values | Destination (octal) | Baseline MCT | Candidate MCT |
| --- | ---: | --- | ---: | ---: |
| Positive | 16,383 | `3466` | 5 | 3 |
| Positive zero | 1 | `3463` | 5 | 3 |
| Negative | 16,383 | `3521` | 5 | 3 |
| Negative zero | 1 | `3463` | 4 | 3 |

All 32,768 cases reached the expected destination and agreed on the watched
state. The negative-zero path adds an explicit branch to the low-word check
to preserve layout. The [optimization record](../../optimizations/waitlist-direct-ccs.json)
links the measurements to the original code. Results were reproduced on
Windows with Zig and on Linux with GCC.

The probe starts each case from a fixed register state with interrupts
inhibited and uses the yaAGC headless I/O stub. Observations end at the first
destination and cover the raw accumulators, selected erasable words, bank
registers, index and selected CPU flags. Scheduler timing and downstream
mission behavior remain outside the measured scope.
