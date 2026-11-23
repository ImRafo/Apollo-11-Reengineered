# Development setup

Install Python 3.11 or newer and Git, then clone the project.

```sh
git clone https://github.com/ImRafo/Apollo-11-Reengineered.git
cd Apollo-11-Reengineered
python -m venv .venv
```

Activate the environment using the command for your shell.

| Shell | Command |
| --- | --- |
| PowerShell | `.venv\Scripts\Activate.ps1` |
| POSIX shell | `. .venv/bin/activate` |

```sh
python -m pip install -e .
python -m pip install -r requirements-dev.txt
apollo-agc --help
```

Build and lint tools are development dependencies. Python CLI commands
use only the standard library at runtime. For yaYUL, oct2bin and yaAGC,
follow the [historical build guide](HISTORICAL_BUILD.md). Builds and local
environments are ignored by Git.
