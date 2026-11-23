# Contributing

Start with the [development setup](docs/DEVELOPMENT_SETUP.md) and the
[testing guide](docs/TESTING.md). Keep a change focused enough to review
and reproduce.

1. Branch from `main` and describe the problem or research question.
2. Implement the change with an appropriate regression test or evidence.
3. Run the relevant checks and review `git diff --check`.
4. Use a descriptive Conventional Commit, for example
   `fix: retain signed relative labels in source comparisons`.
5. Open a pull request with the commands run, observed results, affected
   scope and any remaining limitations.

For historical transcription changes, identify the source scan, page and
line, and explain the assembled-word impact. For experiments, work from
an isolated copy and follow the
[optimization methodology](docs/OPTIMIZATION_METHODOLOGY.md).
Contributions of original tools and documentation use the
[Apache-2.0 license](LICENSE). Preserve the
[historical notices](docs/HISTORICAL_SOURCES.md).
