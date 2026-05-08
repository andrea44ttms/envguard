"""CLI entry-point for the env linter."""
from __future__ import annotations

import json
import sys
from typing import Optional

from envguard.loader import load_env_file
from envguard.linter import lint_env
from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType


def _build_demo_schema() -> EnvSchema:
    schema = EnvSchema()
    schema.add(EnvVarSchema("APP_ENV", EnvVarType.STRING, required=True))
    schema.add(EnvVarSchema("PORT", EnvVarType.INTEGER, required=True))
    schema.add(EnvVarSchema("DEBUG", EnvVarType.BOOLEAN, required=False, default="false"))
    schema.add(EnvVarSchema("SECRET_KEY", EnvVarType.STRING, required=True))
    return schema


def cmd_lint(
    env_path: str,
    schema: Optional[EnvSchema] = None,
    fmt: str = "text",
) -> int:
    """Load *env_path*, run lint checks, print results.

    Returns 0 if no errors, 1 otherwise.
    """
    schema = schema or _build_demo_schema()

    try:
        env = load_env_file(env_path)
    except FileNotFoundError:
        print(f"[ERROR] File not found: {env_path}", file=sys.stderr)
        return 2

    result = lint_env(env, schema)

    if fmt == "json":
        data = [
            {"key": i.key, "message": i.message, "severity": i.severity}
            for i in result.issues
        ]
        print(json.dumps(data, indent=2))
    else:
        print(str(result))

    return 1 if result.error_count > 0 else 0


if __name__ == "__main__":  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description="Lint a .env file.")
    parser.add_argument("env_file", help="Path to .env file")
    parser.add_argument(
        "--format", choices=["text", "json"], default="text", dest="fmt"
    )
    args = parser.parse_args()
    sys.exit(cmd_lint(args.env_file, fmt=args.fmt))
