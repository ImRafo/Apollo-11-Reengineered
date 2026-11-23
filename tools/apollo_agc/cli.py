"""Command-line interface for the AGC research tools."""

import argparse
import json
import sys
from pathlib import Path

from .analysis import analyze, format_analysis
from .comparison import compare, format_comparison
from .listing import analyze_listing, format_listing


def render(report: dict, formatter, output_format: str) -> None:
    print(
        json.dumps(report, indent=2) if output_format == "json" else formatter(report)
    )


def add_output_format(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--format", choices=("text", "json"), default="text")


def run_analysis(args: argparse.Namespace) -> int:
    report = analyze(args.paths)
    render(report, format_analysis, args.format)
    return int(args.strict and report["totals"]["malformed"] > 0)


def run_comparison(args: argparse.Namespace) -> int:
    render(compare(args.before, args.after), format_comparison, args.format)
    return 0


def run_memory(args: argparse.Namespace) -> int:
    render(analyze_listing(args.listing), format_listing, args.format)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="apollo-agc")
    commands = parser.add_subparsers(dest="command", required=True)

    analysis = commands.add_parser("analyze", help="report on Block II source files")
    analysis.add_argument(
        "paths", type=Path, nargs="+", help="source files or directories"
    )
    analysis.add_argument(
        "--strict",
        action="store_true",
        help="exit with an error if malformed lines are reported",
    )
    add_output_format(analysis)
    analysis.set_defaults(handler=run_analysis)

    comparison = commands.add_parser(
        "compare", help="compare two Block II source files"
    )
    comparison.add_argument("before", type=Path)
    comparison.add_argument("after", type=Path)
    add_output_format(comparison)
    comparison.set_defaults(handler=run_comparison)

    memory = commands.add_parser(
        "memory", help="inspect fixed-bank usage in a yaYUL listing"
    )
    memory.add_argument("listing", type=Path)
    add_output_format(memory)
    memory.set_defaults(handler=run_memory)

    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except (OSError, ValueError) as error:
        print(f"{parser.prog}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
