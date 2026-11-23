# Testing

From an activated [development environment](DEVELOPMENT_SETUP.md), run
the same checks as Python CI.

```sh
python -m compileall -q tools scripts tests
python -m unittest discover -s tests -v
python -m ruff check tools scripts tests
python -m ruff format --check tools scripts tests
python -m build
python -m twine check --strict dist/*
```

The unit suite covers representative source lines and both historical
archives, UTF-8 decoding and read failures, CLI exits, JSON output,
duplicate instructions, source order, bank boundaries, listing rows,
optimization records and binary difference location.

Python CI tests installed commands on Linux and Windows with Python 3.11
and 3.14. The quality job validates a wheel and source distribution.
The historical workflow uses the pinned Virtual AGC source, compares the
Luminary rope byte for byte, exports fixed-bank analysis and checks the
headless boot checkpoint. These integration checks are also available
locally through the [historical build guide](HISTORICAL_BUILD.md).
