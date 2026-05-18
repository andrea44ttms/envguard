"""CLI commands for env archiving."""
from __future__ import annotations

import argparse
import sys

from envguard.archiver import archive_env, load_archive_index
from envguard.loader import EnvFileNotFoundError, load_env_file


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envguard-archive",
        description="Archive .env files to a timestamped store.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    save_p = sub.add_parser("save", help="Archive an env file.")
    save_p.add_argument("env_file", help="Path to .env file.")
    save_p.add_argument("--dir", default=".envarchive", help="Archive directory.")
    save_p.add_argument("--no-redact", action="store_true", help="Disable redaction.")
    save_p.add_argument("--prefix", default="envguard", help="Filename prefix.")

    list_p = sub.add_parser("list", help="List archived snapshots.")
    list_p.add_argument("--dir", default=".envarchive", help="Archive directory.")

    return p


def cmd_archive(args: argparse.Namespace) -> int:
    if args.command == "save":
        try:
            env = load_env_file(args.env_file)
        except EnvFileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        result = archive_env(
            env,
            directory=args.dir,
            redact=not args.no_redact,
            prefix=args.prefix,
        )
        print(f"Archived → {result.entry.path}  ({result.entry.key_count} keys)")
        return 0

    if args.command == "list":
        index = load_archive_index(args.dir)
        print(str(index))
        return 0

    return 1


def main() -> None:  # pragma: no cover
    parser = _build_arg_parser()
    sys.exit(cmd_archive(parser.parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()
