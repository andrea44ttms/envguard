"""CLI entry-point for the expiry checker."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from typing import List, Optional

from envguard.expirer import check_expiry
from envguard.loader import EnvFileNotFoundError, EnvParseError, load_env_file


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envguard-expiry",
        description="Check whether date-valued env vars have expired.",
    )
    p.add_argument("env_file", help="Path to .env file")
    p.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        required=True,
        help="Keys to inspect for expiry dates",
    )
    p.add_argument(
        "--ref-date",
        metavar="YYYY-MM-DD",
        help="Reference date (default: today)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
    )
    return p


def cmd_expiry(args: argparse.Namespace) -> int:
    try:
        env = load_env_file(args.env_file)
    except EnvFileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except EnvParseError as exc:
        print(f"parse error: {exc}", file=sys.stderr)
        return 2

    ref: Optional[date] = None
    if args.ref_date:
        try:
            ref = date.fromisoformat(args.ref_date)
        except ValueError:
            print(f"error: invalid ref-date '{args.ref_date}'", file=sys.stderr)
            return 2

    report = check_expiry(env, args.keys, reference_date=ref)

    if args.fmt == "json":
        payload = {
            "expired_count": report.expired_count,
            "entries": [
                {
                    "key": e.key,
                    "expiry_date": e.expiry_date.isoformat(),
                    "is_expired": e.is_expired,
                    "days_remaining": e.days_remaining,
                }
                for e in report.entries
            ],
            "unparseable": report.unparseable,
        }
        print(json.dumps(payload, indent=2))
    else:
        print(report)

    return 1 if report.has_expired else 0


def main(argv: Optional[List[str]] = None) -> None:  # pragma: no cover
    parser = _build_arg_parser()
    sys.exit(cmd_expiry(parser.parse_args(argv)))


if __name__ == "__main__":  # pragma: no cover
    main()
