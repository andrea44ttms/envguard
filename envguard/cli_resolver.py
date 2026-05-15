"""CLI command for resolving env vars across multiple .env files."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envguard.loader import EnvFileNotFoundError, load_env_file
from envguard.resolver import resolve_env


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envguard-resolve",
        description="Resolve effective env var values across multiple .env files (last file wins).",
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help=".env files in ascending priority order (last has highest priority)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "dotenv"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--show-source",
        action="store_true",
        help="Include source file name in text output",
    )
    return parser


def cmd_resolve(args: argparse.Namespace) -> int:
    sources = []
    for path in args.files:
        try:
            env = load_env_file(path)
            sources.append((path, env))
        except EnvFileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    result = resolve_env(sources)

    if args.format == "json":
        data = {
            k: {"value": v.value, "source": v.source}
            for k, v in result.resolved.items()
        }
        print(json.dumps(data, indent=2))

    elif args.format == "dotenv":
        for key, var in sorted(result.resolved.items()):
            print(f"{key}={var.value}")

    else:  # text
        print(f"Resolved {len(result.resolved)} variable(s) from {len(sources)} source(s).")
        for key in sorted(result.resolved):
            var = result.resolved[key]
            if args.show_source:
                print(f"  {key}={var.value!r}  [{var.source}]")
            else:
                print(f"  {key}={var.value!r}")

    return 0


def main(argv: List[str] | None = None) -> None:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    sys.exit(cmd_resolve(args))


if __name__ == "__main__":
    main()
