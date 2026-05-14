"""CLI command for envguard splitter."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envguard.loader import EnvFileNotFoundError, load_env_file
from envguard.splitter import split_env


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envguard-split",
        description="Split a .env file into named buckets by prefix.",
    )
    p.add_argument("env_file", help="Path to the .env file")
    p.add_argument(
        "--prefix",
        dest="prefixes",
        metavar="PREFIX",
        action="append",
        default=[],
        help="Prefix to use as a bucket name (repeatable)",
    )
    p.add_argument(
        "--no-strip",
        dest="strip_prefix",
        action="store_false",
        default=True,
        help="Keep the prefix in bucket keys",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    return p


def cmd_split(args: argparse.Namespace) -> int:
    try:
        env = load_env_file(args.env_file)
    except EnvFileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result = split_env(env, prefixes=args.prefixes, strip_prefix=args.strip_prefix)

    if args.format == "json":
        data = {
            "buckets": result.buckets,
            "unmatched": result.unmatched,
            "total_matched": result.total_matched,
            "unmatched_count": result.unmatched_count,
        }
        print(json.dumps(data, indent=2))
    else:
        print(result)

    return 0


def main(argv: List[str] | None = None) -> None:  # pragma: no cover
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    sys.exit(cmd_split(args))


if __name__ == "__main__":  # pragma: no cover
    main()
