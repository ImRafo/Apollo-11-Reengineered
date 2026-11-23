# AGC Block II constraints

The Apollo 11 Command Module and Lunar Module each had a Block II AGC. Core
rope provided 36,864 fixed words, and magnetic core provided 2,048 erasable
words. An ordinary stored word consists of 15 information bits and an odd
parity bit. One memory cycle is approximately 11.7 microseconds.
[NASA primary guidance and navigation report](https://ntrs.nasa.gov/citations/19760016247)
and [MIT computer characteristics report](https://ntrs.nasa.gov/citations/19670026750).

## Memory and address selection

| CPU address (octal) | Addressed memory |
| --- | --- |
| `0000–1377` | Unswitched erasable, including special registers |
| `1400–1777` | Erasable selected by EB |
| `2000–3777` | Fixed memory selected by FB and the superbank bit |
| `4000–5777` | Fixed-fixed bank `02` |
| `6000–7777` | Fixed-fixed bank `03` |

The erasable store has eight banks of 256 words. The fixed store has 36 banks
of 1,024 words, numbered `00–43` in octal. EB and FB fields are also accessible
through BB. A change in placement can affect reachability and the bank context
observed by a caller. The listing analyzer reports fixed bank and bank-relative
offset so the switched and fixed-fixed address forms can be reconciled.
[Virtual AGC Block II assembly manual](https://www.ibiblio.org/apollo/assembly_language_manual.html).

## Arithmetic, control and timing

Block II uses one's-complement arithmetic. Positive zero is `00000` and
negative zero is `77777` in a 15-bit word. Addition uses end-around carry.
A and Q expose a 16-bit form with overflow considerations, while ordinary
erasable storage uses 15 information bits. Changes that appear algebraically
equivalent can affect sign, overflow, or skip behavior.

Subroutine linkage uses Q, and Z is the program counter. Preserve relevant
registers, editing-register effects, bank state, and the behavior of basic
and extended instruction sequences. Test interrupt and restart paths when
they can observe the changed state. Cycle costs depend on the executed paths
and can be affected by interrupt or counter activity. An interpreter source
statement can contain paired operations and use separate operand words.
[Virtual AGC Block II assembly manual](https://www.ibiblio.org/apollo/assembly_language_manual.html).

yaYUL can insert a checksum word into a fixed bank. A gap in source
or a zero in a rope image is insufficient evidence that an address can be
allocated safely. Use the assembled listing, checksum placement and the
routine's context together. [yaYUL documentation](https://www.ibiblio.org/apollo/yaYUL.html).
