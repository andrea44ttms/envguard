"""CLI command: envguard inspect — display metadata for env vars."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from envguard.loader import load_env_file, EnvFileNotFoundError
from envguard.inspector import inspect_env
from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType


def _build_demo_schema() -> EnvSchema:
    schema = EnvSchema()
    schema.add(EnvVarSchema("DATABASE_URL", type=EnvVarType.STRING, required=True, tags=["db"]))
    schema.add(EnvVarSchema("DB_PASSWORD", type=EnvVarType.STRING, required=True, tags=["db", "secret"]))
    schema.add(EnvVarSchema("PORT", type=EnvVarType.INTEGER, required=False, default="8080"))
    schema.add(EnvVarSchema("DEBUG", type=EnvVarType.BOOLEAN, required=False, default="false"))
    return schema


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envguard-inspect",
        description="Inspect env vars and display type/metadata information.",
    )
    p.add_argument("env_file", help="Path to the .env file")
    p.add_argument("--keys", nargs="+", metavar="KEY", help="Inspect only these keys")
    p.add_argument("--format", choices=["text", "json"], default="text", dest="fmt")
    return p


def cmd_inspect(args: argparse.Namespace) -> int:
    try:
        env = load_env_file(args.env_file)
    except (EnvFileNotFoundError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    schema = _build_demo_schema()
    result = inspect_env(env, schema)

    inspections = result.inspections
    if getattr(args, "keys", None):
        inspections = [i for i in inspections if i.key in args.keys]

    if args.fmt == "json":
        data = [
            {
                "key": i.key,
                "inferred_type": i.inferred_type,
                "declared_type": i.declared_type,
                "is_sensitive": i.is_sensitive,
                "is_declared": i.is_declared,
                "is_required": i.is_required,
                "default": i.default_value,
                "tags": i.tags,
            }
            for i in inspections
        ]
        print(json.dumps(data, indent=2))
    else:
        for insp in inspections:
            print(str(insp))
            print()

    return 0


def main() -> None:  # pragma: no cover
    parser = _build_arg_parser()
    args = parser.parse_args()
    sys.exit(cmd_inspect(args))


if __name__ == "__main__":  # pragma: no cover
    main()
