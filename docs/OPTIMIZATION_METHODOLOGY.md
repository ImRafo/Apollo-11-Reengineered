# Optimization methodology

1. Record the program revision, routine, bank and entry points. Reproduce the
   baseline before changing a working copy.
2. Specify the inputs, outputs, clobbered registers, bank selection, memory
   side effects and timing obligations the routine must preserve.
3. Assemble the isolated variant with the same toolchain. Compare the emitted
   words and listing addresses. Record changes to checksum placement, bank
   extent, constants and instruction encodings.
4. Measure execution costs in memory-cycle timings for named paths. State the
   initial bank and register state, interrupt assumptions and emulator revision.
5. Test positive and negative zero, magnitude limits, overflow, carry, all
   branch outcomes, and bank boundaries where relevant. Compare the full
   observable state at matching checkpoints.
6. Run the relevant emulator scenarios, save reproducible evidence, and record
   uncovered cases. Seek review against the source, listing and test inputs.

Use the [proposal template](../optimizations/proposal.template.json) to record
the original and modified assembly, rationale, memory and timing evidence,
equivalence checks, emulator checks and limitations. A proposed metric stays
`null` until measured. A passing or failing test includes an evidence reference.
A verified report has at least one measured metric and passing records for
both equivalence and emulator checks. Verification applies to the documented
inputs and hardware-state assumptions.

The repository starts with a reproduced baseline and a bounded boot check.
The first verified assembly optimization remains a roadmap milestone.
