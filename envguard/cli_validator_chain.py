"""CLI entry point for the validator chain feature."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envguard.loader import load_env_file, EnvFileNotFoundError
from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType
from envguard.validator_chain import ChainStep, run_chain


def _build_demo_schema() -> EnvSchema:
    schema = EnvSchema()
    schema.add(EnvVarSchema("APP_ENV", type=EnvVarType.STRING, required=True))
    schema.add(EnvVarSchema("PORT", type=EnvVarType.INTEGER, required=True))
    schema.add(EnvVarSchema("DEBUG", type=EnvVarType.BOOLEAN, required=False, default="false"))
    return schema


def cmd_chain(args: argparse.Namespace) -> int:
    schema = _build_demo_schema()
    steps: List[ChainStep] = []

    for i, path in enumerate(args.files):
        try:
            env = load_env_file(path)
        except EnvFileNotFoundError:
            print(f"[error] File not found: {path}", file=sys.stderr)
            return 2
        steps.append(ChainStep(name=f"step-{i+1}:{path}", schema=schema, env=env))

    result = run_chain(steps, stop_on_first_failure=args.stop_on_failure)

    if args.format == "json":
        out = {
            "ok": result.ok,
            "total_errors": result.total_errors,
            "failed_steps": result.failed_steps,
            "steps": [
                {
                    "name": name,
                    "valid": r.is_valid,
                    "errors": [str(e) for e in r.errors],
                }
                for name, r in result.steps
            ],
        }
        print(json.dumps(out, indent=2))
    else:
        print(str(result))
        if not result.ok:
            for name in result.failed_steps:
                for err in result.errors_for(name):
                    print(f"  [{name}] {err}")

    return 0 if result.ok else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Run envguard validation chain over multiple .env files.")
    parser.add_argument("files", nargs="+", help=".env files to validate in order")
    parser.add_argument("--stop-on-failure", action="store_true", help="Halt chain on first failing step")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()
    sys.exit(cmd_chain(args))


if __name__ == "__main__":
    main()
