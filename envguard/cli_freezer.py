"""CLI commands for env freeze/restore/diff operations."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

from envguard.freezer import diff_frozen, freeze_env, load_freeze, save_freeze
from envguard.loader import EnvFileNotFoundError, EnvParseError, load_env_file


def cmd_freeze(args) -> int:
    """Capture the current env file and write a freeze file."""
    try:
        env = load_env_file(args.env_file)
    except EnvFileNotFoundError:
        print(f"Error: env file not found: {args.env_file}", file=sys.stderr)
        return 2
    except EnvParseError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    redact = not getattr(args, "no_redact", False)
    frozen = freeze_env(env, redact=redact)
    output = getattr(args, "output", "env.freeze.json")
    save_freeze(frozen, output)
    print(f"Frozen {len(frozen.values)} variable(s) to {output}")
    return 0


def cmd_show(args) -> int:
    """Display a previously saved freeze file."""
    try:
        frozen = load_freeze(args.freeze_file)
    except FileNotFoundError:
        print(f"Error: freeze file not found: {args.freeze_file}", file=sys.stderr)
        return 2

    if getattr(args, "json", False):
        print(json.dumps(frozen.to_dict(), indent=2))
    else:
        print(f"Captured at : {frozen.captured_at}")
        print(f"Variables   : {len(frozen.values)}")
        print(f"Redacted    : {len(frozen.redacted_keys)}")
        print()
        for k, v in frozen.values.items():
            print(f"  {k}={v}")
    return 0


def cmd_diff(args) -> int:
    """Diff a freeze file against a current env file."""
    try:
        frozen = load_freeze(args.freeze_file)
    except FileNotFoundError:
        print(f"Error: freeze file not found: {args.freeze_file}", file=sys.stderr)
        return 2

    try:
        current = load_env_file(args.env_file)
    except EnvFileNotFoundError:
        print(f"Error: env file not found: {args.env_file}", file=sys.stderr)
        return 2

    redact = not getattr(args, "no_redact", False)
    changes = diff_frozen(frozen, current, redact=redact)

    if not changes:
        print("No changes detected.")
        return 0

    print(f"{len(changes)} change(s) detected:")
    for key, delta in changes.items():
        before = delta["before"] if delta["before"] is not None else "<missing>"
        after = delta["after"] if delta["after"] is not None else "<missing>"
        print(f"  {key}: {before!r} -> {after!r}")
    return 1
