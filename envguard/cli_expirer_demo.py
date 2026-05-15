"""Quick demo for the expiry checker — run directly to see sample output."""
from __future__ import annotations

import argparse
import sys
from datetime import date

from envguard.expirer import check_expiry

_DEMO_ENV = {
    "SSL_CERT_EXPIRY": "2023-12-31",
    "API_TOKEN_EXPIRY": "2025-06-30",
    "DB_PASSWORD_ROTATED": "2024-07-01",
    "OAUTH_SECRET_EXPIRY": "not-set",
}

_DEMO_KEYS = [
    "SSL_CERT_EXPIRY",
    "API_TOKEN_EXPIRY",
    "DB_PASSWORD_ROTATED",
    "OAUTH_SECRET_EXPIRY",
]


def _args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="envguard expiry demo")
    p.add_argument(
        "--ref-date",
        default="2024-06-15",
        metavar="YYYY-MM-DD",
        help="Reference date (default: 2024-06-15)",
    )
    return p.parse_args(argv)


def run_demo(argv=None) -> None:
    args = _args(argv)
    ref = date.fromisoformat(args.ref_date)
    print(f"Reference date: {ref}\n")

    report = check_expiry(_DEMO_ENV, _DEMO_KEYS, reference_date=ref)
    print(report)

    if report.has_expired:
        print(f"\n⚠  {report.expired_count} variable(s) have expired.")
        sys.exit(1)
    else:
        print("\n✓  All checked variables are within their expiry date.")
        sys.exit(0)


if __name__ == "__main__":  # pragma: no cover
    run_demo()
