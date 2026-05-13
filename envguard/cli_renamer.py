"""CLI entry-point for the env-variable renamer."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Dict

from envguard.loader import load_env_file, EnvFileNotFoundError, EnvParseError
from envguard.renamer import rename_env


def _parse_mapping(pairs: list[str]) -> Dict[str, str]:
    """Convert ['OLD=NEW', ...] into a dict."""
    mapping: Dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise argparse.ArgumentTypeError(
                f"Invalid mapping '{pair}': expected OLD=NEW format."
            )
        old, new = pair.split("=", 1)
        mapping[old.strip()] = new.strip()
    return mapping


def cmd_rename(args: argparse.Namespace) -> int:
    """Run the rename command; returns an exit code."""
    try:
        env = load_env_file(args.env_file)
    except EnvFileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except EnvParseError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    try:
        mapping = _parse_mapping(args.rename)
    except argparse.ArgumentTypeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    result = rename_env(env, mapping, overwrite=args.overwrite)

    if args.json:
        print(json.dumps({"renamed": result.renamed, "applied": result.applied, "skipped": result.skipped}, indent=2))
    else:
        print(result)

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="envguard-rename",
        description="Rename keys in a .env file.",
    )
    parser.add_argument("env_file", help="Path to the .env file")
    parser.add_argument(
        "--rename",
        metavar="OLD=NEW",
        nargs="+",
        required=True,
        help="One or more OLD=NEW rename pairs",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting an existing target key",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    return cmd_rename(parser.parse_args(argv))


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
