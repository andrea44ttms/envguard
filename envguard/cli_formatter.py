"""CLI command: format and display typed env values from a .env file."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

from envguard.loader import load_env_file
from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType
from envguard.validator import EnvValidator
from envguard.formatter import format_env
from envguard.redactor import is_sensitive


def _build_demo_schema() -> EnvSchema:
    s = EnvSchema()
    s.add("PORT", EnvVarSchema(type=EnvVarType.INTEGER, required=True))
    s.add("DEBUG", EnvVarSchema(type=EnvVarType.BOOLEAN, required=False, default="false"))
    s.add("APP_NAME", EnvVarSchema(type=EnvVarType.STRING, required=True))
    s.add("TIMEOUT", EnvVarSchema(type=EnvVarType.FLOAT, required=False, default="30.0"))
    s.add("SECRET_KEY", EnvVarSchema(type=EnvVarType.STRING, required=False))
    return s


def _apply_redaction(data: dict, redact: bool) -> dict:
    """Return a copy of data with sensitive values masked if redact is True."""
    if not redact:
        return data
    return {k: ("***" if is_sensitive(k) else v) for k, v in data.items()}


def _print_table(data: dict) -> None:
    """Print env data as a formatted table to stdout."""
    print(f"{'Key':<25} {'Type':<10} Value")
    print("-" * 55)
    for key, value in data.items():
        type_name = type(value).__name__
        print(f"{key:<25} {type_name:<10} {value}")


def cmd_format(
    env_path: str,
    schema: Optional[EnvSchema] = None,
    output_json: bool = False,
    redact: bool = True,
) -> int:
    """Load, validate, and display typed env values.

    Returns 0 on success, 1 on validation failure.
    """
    path = Path(env_path)
    if not path.exists():
        print(f"[envguard] File not found: {env_path}", file=sys.stderr)
        return 1

    raw = load_env_file(str(path))
    s = schema or _build_demo_schema()

    validator = EnvValidator(s)
    result = validator.validate(raw)

    formatted = format_env(raw, s, result)
    data = formatted.to_dict()
    data = _apply_redaction(data, redact)

    if output_json:
        print(json.dumps(data, indent=2, default=str))
    else:
        _print_table(data)

    if not result.is_valid:
        print(f"\n[envguard] Validation failed: {result.error_count} error(s).", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description="Format and display typed env values.")
    parser.add_argument("env_file", help="Path to .env file")
    parser.add_argument("--json", action="store_true", dest="output_json", help="Output as JSON")
    parser.add_argument("--no-redact", action="store_false", dest="redact", help="Show sensitive values")
    args = parser.parse_args()
    sys.exit(cmd_format(args.env_file, output_json=args.output_json, redact=args.redact))
