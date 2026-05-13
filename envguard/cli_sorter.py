"""CLI entry-point for the env sorter."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envguard.loader import load_env_file
from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType
from envguard.sorter import SortOrder, sort_env


def _build_demo_schema() -> EnvSchema:
    schema = EnvSchema()
    schema.add(EnvVarSchema("DATABASE_URL", type=EnvVarType.STRING, required=True))
    schema.add(EnvVarSchema("DB_PORT", type=EnvVarType.INTEGER, required=True))
    schema.add(EnvVarSchema("DEBUG", type=EnvVarType.BOOLEAN, required=False, default="false"))
    schema.add(EnvVarSchema("APP_NAME", type=EnvVarType.STRING, required=False, default="myapp"))
    schema.add(EnvVarSchema("MAX_RETRIES", type=EnvVarType.INTEGER, required=False, default="3"))
    return schema


def cmd_sort(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="envguard-sort",
        description="Sort .env variables by a chosen order.",
    )
    parser.add_argument("env_file", help="Path to the .env file")
    parser.add_argument(
        "--order",
        choices=[o.value for o in SortOrder],
        default=SortOrder.ALPHA.value,
        help="Sort order (default: alpha)",
    )
    parser.add_argument("--show-sections", action="store_true",
                        help="Print section groupings when available")
    args = parser.parse_args(argv)

    try:
        env = load_env_file(args.env_file)
    except FileNotFoundError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2

    schema = _build_demo_schema()
    order = SortOrder(args.order)
    result = sort_env(env, schema, order=order)

    print(f"Sort order: {result.order.value}")
    print(f"Variables : {len(result.sorted_env)}")
    if args.show_sections and result.sections:
        for section, keys in result.sections.items():
            print(f"  [{section}] {', '.join(keys)}")
    print()
    for key, value in result.sorted_env.items():
        print(f"{key}={value}")

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(cmd_sort())
