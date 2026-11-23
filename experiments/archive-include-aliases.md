# Luminary archive include aliases

**Question.** Can the archived GitHub transcription reproduce the
proofed rope when its two missing include names are supplied?

## Procedure

Run the [historical toolchain setup](../docs/HISTORICAL_BUILD.md), then run
the two archive modes in separate output directories.

```sh
python scripts/reproduce_luminary.py --source archive --output build/luminary-archive
python scripts/reproduce_luminary.py --source archive-aliases --output build/luminary-aliases
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
representation bit, so they differ from the 15-bit values printed in the
assembly listing. The two include aliases are enough to build an image.
The two object-word differences still need to be traced to the source scans,
and the resulting image has no equivalence or emulator result in this experiment.
