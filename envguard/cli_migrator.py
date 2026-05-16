"""CLI entry-point for the env migrator."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envguard.loader import load_env_file, EnvFileNotFoundError
from envguard.migrator import MigrationStep, migrate_env


def _parse_steps(rename_pairs: List[str], patch_pairs: List[str]) -> List[MigrationStep]:
    steps: List[MigrationStep] = []
    for pair in rename_pairs:
        if ":" not in pair:
            print(f"[warn] invalid rename pair (expected OLD:NEW): {pair!r}", file=sys.stderr)
            continue
        old, new = pair.split(":", 1)
        steps.append(MigrationStep(action="rename", key=old.strip(), new_key=new.strip()))
    for pair in patch_pairs:
        if "=" not in pair:
            print(f"[warn] invalid patch pair (expected KEY=VALUE): {pair!r}", file=sys.stderr)
            continue
        key, value = pair.split("=", 1)
        steps.append(MigrationStep(action="patch", key=key.strip(), value=value))
    return steps


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envguard-migrate",
        description="Apply rename/patch migration steps to a .env file.",
    )
    p.add_argument("file", help="Path to the .env file")
    p.add_argument("-r", "--rename", metavar="OLD:NEW", action="append", default=[],
                   help="Rename a key (repeatable)")
    p.add_argument("-p", "--patch", metavar="KEY=VALUE", action="append", default=[],
                   help="Set / overwrite a key (repeatable)")
    p.add_argument("--format", choices=["text", "json", "dotenv"], default="text")
    return p


def cmd_migrate(args: argparse.Namespace) -> int:
    try:
        env = load_env_file(args.file)
    except (EnvFileNotFoundError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    steps = _parse_steps(args.rename, args.patch)
    result = migrate_env(env, steps)

    if args.format == "json":
        print(json.dumps({
            "apply_count": result.apply_count,
            "skip_count": result.skip_count,
            "migrated": result.migrated,
        }, indent=2))
    elif args.format == "dotenv":
        for k, v in result.migrated.items():
            print(f"{k}={v}")
    else:
        print(result)

    return 0


def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()
    sys.exit(cmd_migrate(args))


if __name__ == "__main__":
    main()
