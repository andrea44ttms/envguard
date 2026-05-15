"""CLI entry-point for the env filter command."""
from __future__ import annotations

import argparse
import json
import sys

from envguard.filter import filter_env
from envguard.loader import EnvFileNotFoundError, EnvParseError, load_env_file


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envguard filter",
        description="Filter env vars by glob pattern.",
    )
    p.add_argument("env_file", help="Path to .env file")
    p.add_argument(
        "--pattern",
        dest="patterns",
        metavar="GLOB",
        action="append",
        default=None,
        help="Glob pattern to match keys (repeatable)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json", "dotenv"],
        default="text",
        help="Output format",
    )
    p.add_argument(
        "--name",
        default="cli",
        help="Label for this filter run",
    )
    return p


def _write_output(result: object, fmt: str) -> None:
    """Write *result* to stdout in the requested *fmt*.

    Supported formats:
    - ``json``   – JSON object with ``matched`` and ``excluded`` keys.
    - ``dotenv`` – KEY=value lines for matched keys only.
    - ``text``   – Human-readable string representation of the result.
    """
    if fmt == "json":
        print(json.dumps({"matched": result.matched, "excluded": result.excluded}))
    elif fmt == "dotenv":
        for k, v in result.matched.items():
            print(f"{k}={v}")
    else:
        print(result)


def cmd_filter(args: argparse.Namespace) -> int:
    """Execute the filter sub-command and return an exit code."""
    try:
        env = load_env_file(args.env_file)
    except EnvFileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except EnvParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result = filter_env(
        env,
        patterns=args.patterns,
        filter_name=args.name,
    )

    _write_output(result, args.format)

    return 0


def main() -> None:  # pragma: no cover
    parser = _build_arg_parser()
    sys.exit(cmd_filter(parser.parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()
