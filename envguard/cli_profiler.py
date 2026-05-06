"""CLI command for profiling a .env file against a schema."""

from __future__ import annotations

import json
import sys
from typing import Dict

from envguard.loader import load_env_file
from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType
from envguard.validator import EnvValidator
from envguard.profiler import profile_env


def _build_demo_schema() -> EnvSchema:
    """Return a minimal demo schema for standalone CLI usage."""
    s = EnvSchema()
    s.add(EnvVarSchema(name="APP_NAME", type=EnvVarType.STRING, required=True))
    s.add(EnvVarSchema(name="PORT", type=EnvVarType.INTEGER, required=False, default="8080"))
    s.add(EnvVarSchema(name="DEBUG", type=EnvVarType.BOOLEAN, required=False, default="false"))
    s.add(EnvVarSchema(name="SECRET_KEY", type=EnvVarType.STRING, required=True))
    return s


def cmd_profile(env_path: str, fmt: str = "text", schema: EnvSchema | None = None) -> int:
    """Profile *env_path* and print results.  Returns exit code."""
    try:
        env: Dict[str, str] = load_env_file(env_path)
    except FileNotFoundError:
        print(f"[envguard] File not found: {env_path}", file=sys.stderr)
        return 1

    if schema is None:
        schema = _build_demo_schema()

    result = EnvValidator(schema).validate(env)
    prof = profile_env(schema, result)

    if fmt == "json":
        data = {
            "total": prof.total,
            "required": prof.required_count,
            "optional": prof.optional_count,
            "by_type": prof.by_type,
            "sensitive_keys": prof.sensitive_keys,
            "with_defaults": prof.with_defaults,
            "with_constraints": prof.with_constraints,
            "error_keys": prof.error_keys,
            "health_score": prof.health_score,
        }
        print(json.dumps(data, indent=2))
    else:
        print(str(prof))

    return 0 if result.is_valid else 1


if __name__ == "__main__":  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description="Profile a .env file")
    parser.add_argument("env_file", help="Path to the .env file")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()
    sys.exit(cmd_profile(args.env_file, fmt=args.format))
