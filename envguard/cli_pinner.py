"""envguard.cli_pinner — CLI commands for env pinning."""
from __future__ import annotations

import argparse
import os
import sys

from envguard.loader import EnvFileNotFoundError, load_env_file
from envguard.pinner import diff_pin, load_pin, pin_env, save_pin

_DEFAULT_LOCK = ".env.lock"


def cmd_pin(args: argparse.Namespace) -> int:
    """Capture current .env and write a lockfile."""
    try:
        env = load_env_file(args.env_file)
    except EnvFileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result = pin_env(env, redact=not args.no_redact, source=args.env_file)
    save_pin(result, args.lock_file)
    print(f"Pinned {result.count} variable(s) → {args.lock_file}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    """Display the contents of a lockfile."""
    result = load_pin(args.lock_file)
    if result is None:
        print(f"error: lockfile not found: {args.lock_file}", file=sys.stderr)
        return 2
    print(f"Pinned at : {result.pinned_at}")
    print(f"Source    : {result.source or '(unknown)'}")
    print(f"Variables : {result.count}")
    print()
    print(str(result))
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """Compare current .env against a lockfile and report drift."""
    try:
        env = load_env_file(args.env_file)
    except EnvFileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    previous = load_pin(args.lock_file)
    if previous is None:
        print(f"error: lockfile not found: {args.lock_file}", file=sys.stderr)
        return 2

    current = pin_env(env, redact=not args.no_redact, source=args.env_file)
    changes = diff_pin(current, previous)

    if not changes:
        print("No drift detected — env matches lockfile.")
        return 0

    print(f"{len(changes)} drift(s) detected:")
    for key, delta in changes.items():
        old = delta["old"] if delta["old"] is not None else "(absent)"
        new = delta["new"] if delta["new"] is not None else "(absent)"
        print(f"  {key}: {old!r} → {new!r}")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="envguard-pin", description="Env pinning tool")
    sub = parser.add_subparsers(dest="command")

    for name, fn in (("pin", cmd_pin), ("show", cmd_show), ("check", cmd_check)):
        p = sub.add_parser(name)
        if name != "show":
            p.add_argument("env_file", nargs="?", default=".env")
            p.add_argument("--no-redact", action="store_true")
        p.add_argument("--lock-file", default=_DEFAULT_LOCK)
        p.set_defaults(func=fn)

    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
