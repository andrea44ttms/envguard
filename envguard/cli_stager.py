"""CLI entry-point for the env stager."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envguard.loader import EnvFileNotFoundError, EnvParseError, load_env_file
from envguard.stager import stage_env


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envguard-stage",
        description="Filter .env variables by deployment stage.",
    )
    p.add_argument("env_file", help="Path to the .env file")
    p.add_argument("stage", help="Stage name (e.g. production, staging, development, test)")
    p.add_argument(
        "--prefix",
        action="append",
        dest="prefixes",
        metavar="PREFIX",
        help="Custom prefix for the stage (repeatable). E.g. --prefix PROD_",
    )
    p.add_argument(
        "--no-strip",
        action="store_true",
        default=False,
        help="Keep the stage prefix in output keys",
    )
    p.add_argument(
        "--format",
        choices=["text", "json", "dotenv"],
        default="text",
        help="Output format (default: text)",
    )
    return p


def cmd_stage(args: argparse.Namespace) -> int:
    try:
        env = load_env_file(args.env_file)
    except EnvFileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except EnvParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    stage_prefixes = None
    if args.prefixes:
        stage_prefixes = {args.stage.lower(): args.prefixes}

    result = stage_env(
        env,
        args.stage,
        stage_prefixes=stage_prefixes,
        strip_prefix=not args.no_strip,
    )

    fmt = args.format
    if fmt == "json":
        print(json.dumps({"stage": result.stage, "matched": result.matched, "excluded_count": result.excluded_count}, indent=2))
    elif fmt == "dotenv":
        for k, v in result.matched.items():
            print(f"{k}={v}")
    else:
        print(str(result))

    return 0


def main(argv: List[str] | None = None) -> None:  # pragma: no cover
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    sys.exit(cmd_stage(args))


if __name__ == "__main__":  # pragma: no cover
    main()
