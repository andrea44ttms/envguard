"""CLI entry-point for the env patcher."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envguard.loader import EnvFileNotFoundError, load_env_file
from envguard.patcher import patch_env, write_patch


def _parse_pairs(pairs: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise argparse.ArgumentTypeError(f"Invalid KEY=VALUE pair: {pair!r}")
        key, _, value = pair.partition("=")
        result[key.strip()] = value.strip()
    return result


def cmd_patch(args: argparse.Namespace) -> int:
    try:
        env = load_env_file(Path(args.file))
    except EnvFileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    updates = _parse_pairs(args.set or [])
    remove = [k.strip() for k in (args.remove or [])]

    result = patch_env(env, updates, remove_keys=remove)

    if args.write:
        write_patch(Path(args.file), result)
        print(f"Patched {args.file}: {result.change_count} change(s).")
    else:
        for line in result.patched_lines:
            print(line)

    return 0


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(description="Patch a .env file in-place or preview changes.")
    parser.add_argument("file", help="Path to .env file")
    parser.add_argument("--set", metavar="KEY=VALUE", nargs="+", help="Set or update key")
    parser.add_argument("--remove", metavar="KEY", nargs="+", help="Remove key")
    parser.add_argument("--write", action="store_true", help="Write changes back to file")
    sys.exit(cmd_patch(parser.parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()
