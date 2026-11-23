# Roadmap

Version labels describe milestones. A milestone can use prototypes that
already exist in the repository and still require more evidence before release.

| Milestone | Objective | Evidence required |
| --- | --- | --- |
| v0.1.0 | Project Foundation | Attributed archive, maintainable tooling, build instructions, automated checks |
| v0.2.0 | Historical Build Reproduction | Repeatable Luminary reference verification and regression coverage for the staged archive corrections |
| v0.3.0 | AGC Analysis Tools | Stable report contracts and broader comparison and listing fixtures |
| v0.4.0 | Automated Regression Testing | Reproducible register, arithmetic, timing and boundary vectors |
| v0.5.0 | First Verified Assembly Optimization | Source, binary and timing comparison with passing equivalence and emulator results |
| v0.6.0 | Execution and Memory Profiling | Path-level cycle and bank measurements reproduced from traces |
| v0.7.0 | Experimental AGC Enhancements | Isolated experiments with documented Block II assumptions and results |
| v1.0.0 | Documented Research Platform | Reproducible workflows, stable interfaces and reviewable research records |

The headless Luminary boot check and initial analysis tools are present.
The [archive experiment](experiments/archive-include-aliases.md) now
reproduces the proofed rope using a staged copy. The next objective is
to establish equivalence fixtures for a small routine, including signed
zero, overflow and observable register effects at matching checkpoints.
