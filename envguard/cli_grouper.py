"""CLI command for grouping env variables by prefix."""
from __future__ import annotations
import argparse
import sys
from envguard.loader import load_env_file
from envguard.grouper import group_by_prefix
from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType


def _build_demo_schema() -> EnvSchema:
    schema = EnvSchema()
    for key, t in [
        ("DB_HOST", EnvVarType.STRING),
        ("DB_PORT", EnvVarType.INTEGER),
        ("DB_NAME", EnvVarType.STRING),
        ("AWS_ACCESS_KEY", EnvVarType.STRING),
        ("AWS_SECRET", EnvVarType.STRING),
        ("APP_DEBUG", EnvVarType.BOOLEAN),
        ("APP_PORT", EnvVarType.INTEGER),
        ("LOG_LEVEL", EnvVarType.STRING),
    ]:
        schema.add(EnvVarSchema(name=key, type=t, required=True))
    return schema


def cmd_group(args: argparse.Namespace) -> int:
    try:
        env = load_env_file(args.env_file)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    schema = _build_demo_schema() if args.use_demo_schema else None
    result = group_by_prefix(
        env,
        schema=schema,
        separator=args.separator,
        min_prefix_length=args.min_prefix,
    )

    print(f"Groups found: {len(result.groups)}")
    print(f"Total grouped vars: {result.total_grouped}")
    print(f"Ungrouped vars: {len(result.ungrouped)}")
    print()
    print(str(result))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Group env vars by prefix")
    parser.add_argument("env_file", help="Path to .env file")
    parser.add_argument("--separator", default="_", help="Prefix separator (default: _)")
    parser.add_argument("--min-prefix", type=int, default=2, dest="min_prefix",
                        help="Minimum prefix length (default: 2)")
    parser.add_argument("--demo-schema", action="store_true", dest="use_demo_schema",
                        help="Use built-in demo schema to filter keys")
    args = parser.parse_args()
    sys.exit(cmd_group(args))


if __name__ == "__main__":
    main()
