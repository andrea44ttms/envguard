"""CLI entry-point for the env rotation auditor."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from envguard.loader import EnvFileNotFoundError, load_env_file
from envguard.rotator import rotate_env


def _parse_custom_reasons(pairs: List[str]) -> dict:
    """Parse KEY=reason strings into a dict."""
    out: dict = {}
    for pair in pairs:
        if "=" not in pair:
            continue
        key, _, reason = pair.partition("=")
        out[key.strip()] = reason.strip()
    return out


def cmd_rotate(args: argparse.Namespace) -> int:
    try:
        env = load_env_file(args.env_file)
    except EnvFileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    custom_reasons = _parse_custom_reasons(args.reason or [])

    report = rotate_env(
        env,
        empty_sensitive=not args.no_empty_check,
        placeholder_pattern=args.placeholder,
        custom_reasons=custom_reasons,
    )

    if args.format == "json":
        data = {
            "count": report.count,
            "sensitive_count": report.sensitive_count,
            "candidates": [
                {"key": c.key, "reason": c.reason, "sensitive": c.sensitive}
                for c in report.candidates
            ],
        }
        print(json.dumps(data, indent=2))
    else:
        print(str(report))

    return 1 if report.has_candidates() else 0


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        prog="envguard-rotate",
        description="Detect env vars that should be rotated.",
    )
    parser.add_argument("env_file", help="Path to the .env file")
    parser.add_argument(
        "--placeholder",
        default="CHANGEME",
        help="Placeholder string that flags a key for rotation (default: CHANGEME)",
    )
    parser.add_argument(
        "--no-empty-check",
        action="store_true",
        help="Skip flagging sensitive keys with empty values",
    )
    parser.add_argument(
        "--reason",
        action="append",
        metavar="KEY=reason",
        help="Mark KEY with a custom rotation reason (repeatable)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    args = parser.parse_args(argv)
    sys.exit(cmd_rotate(args))


if __name__ == "__main__":  # pragma: no cover
    main()
