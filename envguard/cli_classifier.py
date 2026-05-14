"""CLI command for env var classification."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envguard.loader import EnvFileNotFoundError, load_env_file
from envguard.classifier import classify_env


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envguard-classify",
        description="Classify .env variables into semantic categories.",
    )
    p.add_argument("env_file", help="Path to the .env file")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--category",
        metavar="CAT",
        help="Show only variables in this category",
    )
    return p


def cmd_classify(args: argparse.Namespace) -> int:
    try:
        env = load_env_file(args.env_file)
    except EnvFileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result = classify_env(env)

    if args.format == "json":
        data = (
            {args.category: result.vars_for(args.category)}
            if args.category
            else result.categories
        )
        print(json.dumps(data, indent=2))
        return 0

    # Text output
    cats = [args.category] if args.category else result.category_names
    for cat in cats:
        keys = result.vars_for(cat)
        if keys:
            print(f"[{cat}]")
            for k in keys:
                print(f"  {k}")
    return 0


def main(argv: List[str] | None = None) -> None:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    sys.exit(cmd_classify(args))


if __name__ == "__main__":
    main()
