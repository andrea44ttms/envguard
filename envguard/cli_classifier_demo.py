"""Standalone demo for the classifier CLI — no real .env file required."""
from __future__ import annotations

import argparse
import sys
from typing import List

from envguard.classifier import classify_env

_DEMO_ENV = {
    "DATABASE_URL": "postgres://localhost/mydb",
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "REDIS_URL": "redis://localhost:6379",
    "CACHE_TTL": "300",
    "SECRET_KEY": "supersecret",
    "API_KEY": "abc123",
    "AUTH_TOKEN": "tok_xyz",
    "LOG_LEVEL": "INFO",
    "SENTRY_DSN": "https://sentry.io/123",
    "PORT": "8080",
    "HOST": "0.0.0.0",
    "APP_ENV": "production",
    "DEBUG": "false",
    "FOOBAR": "baz",
}


def _args(argv: List[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="envguard-classify-demo",
        description="Demo: classify built-in sample env vars.",
    )
    p.add_argument(
        "--category",
        metavar="CAT",
        help="Filter output to a single category",
    )
    return p.parse_args(argv)


def run_demo(argv: List[str] | None = None) -> int:
    args = _args(argv)
    result = classify_env(_DEMO_ENV)

    cats = [args.category] if args.category else result.category_names
    for cat in cats:
        keys = result.vars_for(cat)
        if not keys:
            continue
        print(f"[{cat}] ({len(keys)} var{'s' if len(keys) != 1 else ''})")
        for k in keys:
            print(f"  {k}")
    return 0


if __name__ == "__main__":
    sys.exit(run_demo())
