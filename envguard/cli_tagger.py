"""CLI command: envguard tag — filter and display env vars by tag."""
from __future__ import annotations

import argparse
import sys
from typing import List

from envguard.loader import load_env_file, EnvFileNotFoundError
from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType
from envguard.tagger import build_tag_index


def _build_demo_schema() -> EnvSchema:
    schema = EnvSchema()
    schema.add("DATABASE_URL", EnvVarSchema(type=EnvVarType.STRING, required=True, tags=["db", "infra"]))
    schema.add("DB_POOL_SIZE", EnvVarSchema(type=EnvVarType.INTEGER, required=False, default="5", tags=["db"]))
    schema.add("SECRET_KEY", EnvVarSchema(type=EnvVarType.STRING, required=True, tags=["security"]))
    schema.add("DEBUG", EnvVarSchema(type=EnvVarType.BOOLEAN, required=False, default="false", tags=["infra"]))
    schema.add("APP_NAME", EnvVarSchema(type=EnvVarType.STRING, required=True))
    return schema


def cmd_tag(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="envguard-tag",
        description="Filter env variables by tag.",
    )
    parser.add_argument("env_file", help="Path to .env file")
    parser.add_argument("tags", nargs="+", help="Tags to filter by")
    parser.add_argument("--list-tags", action="store_true", help="List all available tags and exit")
    args = parser.parse_args(argv)

    try:
        env = load_env_file(args.env_file)
    except EnvFileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    schema = _build_demo_schema()
    index = build_tag_index(schema)

    if args.list_tags:
        print("Available tags:")
        for tag in index.all_tags():
            print(f"  {tag}")
        return 0

    filtered = index.filter_env(env, args.tags)
    if not filtered:
        print(f"No variables found for tags: {', '.join(args.tags)}")
        return 0

    print(f"Variables matching tag(s) [{', '.join(args.tags)}]:")
    for key, value in sorted(filtered.items()):
        print(f"  {key}={value}")
    return 0
