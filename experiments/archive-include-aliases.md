# Luminary archive reproduction

**Question.** Which changes to a working copy of the archived GitHub
transcription are required to reproduce the proofed rope?

## Procedure

Run the [historical toolchain setup](../docs/HISTORICAL_BUILD.md), then run
the three archive modes in separate output directories.

```sh
python scripts/reproduce_luminary.py --source archive --output build/luminary-archive
python scripts/reproduce_luminary.py --source archive-aliases --output build/luminary-aliases
python scripts/reproduce_luminary.py --source archive-normalized --output build/luminary-normalized
```

The alias mode stages these two copies inside the build directory. The
177 archived files retain their original bytes.

| Name requested by `MAIN.agc` | File found in the archive |
| --- | --- |
| `LAMBERT_AIMPOINT_GUIDANCE.agc` | `GENERAL_LAMBERT_AIMPOINT_GUIDANCE.agc` |
| `TRIM_GIMBAL_CNTROL_SYSTEM.agc` | `TRIM_GIMBAL_CONTROL_SYSTEM.agc` |

## Results

The unmodified archive stopped at the first missing include and reported
2,572 fatal errors and 237 unresolved symbols. It did not produce a rope.
With both names present, assembly succeeded and generated a 73,728-byte
image with SHA-256
`bf87398818b99446e300aa319c3e177e42131277f7e83822e8fa0db8ba3008b1`.
The verification command returned an error because four encoded words
differed from the proofed image.

| Bank | Offset | Archive with aliases | Proofed | Listing entry |
| --- | --- | --- | --- | --- |
| `21` | `1373` | `054314` | `120154` | `INDEX QRNDXER` |
| `21` | `1772` | `123076` | `157236` | Bank checksum |
| `33` | `1210` | `063320` | `014076` | `TC INTPRET` |
| `33` | `1777` | `047674` | `017120` | Bank checksum |

Values in the table are octal. Encoded file words include the low
representation bit outside the 15-bit value printed in the assembly listing.

## Relative-label layout

The differing program words come from `SERVICER.agc:1133` and
`TRIM_GIMBAL_CONTROL_SYSTEM.agc:382`. The archived whitespace puts `+3`
and `+2` in column 9 after tab expansion. yaYUL recognizes relative labels
in columns 2 through 8. The normalized variant moves each relative label
into column 2 and aligns its mnemonic at column 17, matching the pinned
transcription. [yaYUL column rules](https://github.com/virtualagc/virtualagc/blob/27b7ae91f0a8f0e9145091dba12eb66d543c529a/yaYUL/Pass.c#L1877-L1892).

With both layout corrections and the include aliases applied to the working
copy, the image matched all 73,728 bytes of the proofed reference. Its SHA-256
is `1f5326e038de5b741b2f27b01ec949dbd688cf1906994e997402587c8628f40e`.
The comparison verifies the output of this specific staging procedure.
