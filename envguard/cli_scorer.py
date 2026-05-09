"""envguard.cli_scorer — CLI command to score a .env file against a schema."""

from __future__ import annotations

import sys
from typing import Optional

from envguard.loader import load_env_file
from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType
from envguard.validator import EnvValidator
from envguard.scorer import score_env


def _build_demo_schema() -> EnvSchema:
    schema = EnvSchema()
    schema.add(EnvVarSchema("APP_ENV", EnvVarType.STRING, required=True))
    schema.add(EnvVarSchema("PORT", EnvVarType.INTEGER, required=True, min_value=1, max_value=65535))
    schema.add(EnvVarSchema("DEBUG", EnvVarType.BOOLEAN, required=False, default="false"))
    schema.add(EnvVarSchema("SECRET_KEY", EnvVarType.STRING, required=True))
    schema.add(EnvVarSchema("MAX_RETRIES", EnvVarType.INTEGER, required=False, default="3"))
    return schema


def cmd_score(env_path: Optional[str] = None, schema: Optional[EnvSchema] = None) -> int:
    """Load *env_path*, validate against *schema*, print the score, return exit code."""
    schema = schema or _build_demo_schema()

    try:
        env = load_env_file(env_path or ".env")
    except FileNotFoundError:
        print(f"[envguard] File not found: {env_path or '.env'}", file=sys.stderr)
        return 2

    validator = EnvValidator(schema)
    result = validator.validate(env)
    env_score = score_env(env, schema, result)

    print(str(env_score))

    if not result.is_valid:
        print("\nValidation errors:")
        for err in result.errors:
            print(f"  - {err}")

    return 0 if result.is_valid else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(cmd_score())
