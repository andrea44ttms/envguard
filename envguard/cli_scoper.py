"""CLI entry-point for the env scoper."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envguard.loader import EnvFileNotFoundError, load_env_file
from envguard.scoper import scope_env


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envguard-scope",
        description="Filter an .env file to a named deployment scope.",
    )
    p.add_argument("env_file", help="Path to the .env file.")
    p.add_argument("scope", help="Target scope name (e.g. production).")
    p.add_argument(
        "--scope-key",
        metavar="KEY=SCOPE",
        action="append",
        dest="scope_keys",
        default=[],
        help="Assign KEY to SCOPE.  Repeat for multiple keys.",
    )
    p.add_argument(
        "--exclude-unscoped",
        action="store_true",
        default=False,
        help="Omit keys that belong to no scope.",
    )
    p.add_argument(
        "--format",
        choices=["text", "json", "dotenv"],
        default="dotenv",
        help="Output format (default: dotenv).",
    )
    return p


def _parse_scope_keys(raw: List[str]) -> dict:
    """Parse ``KEY=SCOPE`` strings into {scope: [key, ...]}."""
    mapping: dict = {}
    for item in raw:
        if "=" not in item:
            continue
        key, scope = item.split("=", 1)
        mapping.setdefault(scope.strip(), []).append(key.strip())
    return mapping


def cmd_scope(args: argparse.Namespace) -> int:
    try:
        env = load_env_file(args.env_file)
    except EnvFileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    scope_map = _parse_scope_keys(args.scope_keys)
    result = scope_env(
        env,
        args.scope,
        scope_map,
        include_unscoped=not args.exclude_unscoped,
    )

    fmt = args.format
    if fmt == "json":
        print(json.dumps({"scope": result.scope,
                          "matched": result.matched,
                          "excluded": result.excluded}, indent=2))
    elif fmt == "text":
        print(str(result))
    else:  # dotenv
        for k, v in result.matched.items():
            print(f"{k}={v}")

    return 0


def main() -> None:  # pragma: no cover
    parser = _build_arg_parser()
    sys.exit(cmd_scope(parser.parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()
