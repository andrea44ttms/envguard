"""CLI command for comparing two .env files against a schema."""

import sys
from envguard.loader import load_env_file
from envguard.comparator import compare_envs
from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType


def _build_demo_schema() -> EnvSchema:
    schema = EnvSchema()
    schema.add(EnvVarSchema("DATABASE_URL", EnvVarType.STRING, required=True))
    schema.add(EnvVarSchema("SECRET_KEY", EnvVarType.STRING, required=True))
    schema.add(EnvVarSchema("DEBUG", EnvVarType.BOOLEAN, required=False, default="false"))
    schema.add(EnvVarSchema("PORT", EnvVarType.INTEGER, required=False, default="8000"))
    return schema


def cmd_compare(args) -> int:
    """
    Compare two .env files and print structural differences.

    Expected args attributes:
        left  : path to the first .env file
        right : path to the second .env file
        redact: bool — whether to redact sensitive values (default True)
    """
    redact: bool = getattr(args, "redact", True)

    try:
        left_env = load_env_file(args.left)
    except Exception as exc:
        print(f"[envguard] ERROR loading left file '{args.left}': {exc}", file=sys.stderr)
        return 2

    try:
        right_env = load_env_file(args.right)
    except Exception as exc:
        print(f"[envguard] ERROR loading right file '{args.right}': {exc}", file=sys.stderr)
        return 2

    schema = _build_demo_schema() if redact else None
    comparison = compare_envs(left_env, right_env, schema=schema)

    print(f"Comparing: {args.left}  vs  {args.right}")
    print("-" * 48)
    print(comparison)

    return 1 if comparison.has_differences else 0
