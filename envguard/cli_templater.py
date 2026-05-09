"""CLI command for generating .env templates from a schema."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType
from envguard.templater import TemplateOptions, generate_template


def _build_demo_schema() -> EnvSchema:
    schema = EnvSchema()
    schema.add("APP_NAME", EnvVarSchema(type=EnvVarType.STRING, required=True, description="Application name"))
    schema.add("PORT", EnvVarSchema(type=EnvVarType.INTEGER, required=False, default=8080, description="HTTP port"))
    schema.add("DEBUG", EnvVarSchema(type=EnvVarType.BOOLEAN, required=False, default=False, description="Enable debug mode"))
    schema.add("DATABASE_URL", EnvVarSchema(type=EnvVarType.STRING, required=True, description="Postgres connection string"))
    schema.add("SECRET_KEY", EnvVarSchema(type=EnvVarType.STRING, required=True, description="App secret key"))
    return schema


def cmd_template(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="envguard-template",
        description="Generate a .env template from a schema.",
    )
    parser.add_argument("--output", "-o", default="-", help="Output file path (default: stdout)")
    parser.add_argument("--no-comments", action="store_true", help="Omit comments from output")
    parser.add_argument("--no-defaults", action="store_true", help="Omit default values from output")
    parser.add_argument(
        "--placeholder",
        default="<{name}>",
        help="Placeholder style for required vars (default: '<{name}>')",
    )
    args = parser.parse_args(argv)

    schema = _build_demo_schema()
    options = TemplateOptions(
        include_comments=not args.no_comments,
        include_defaults=not args.no_defaults,
        placeholder_style=args.placeholder,
    )
    result = generate_template(schema, options)

    if args.output == "-":
        sys.stdout.write(result.content)
    else:
        Path(args.output).write_text(result.content, encoding="utf-8")
        print(f"Template written to {args.output} ({result.var_count} vars: "
              f"{result.required_count} required, {result.optional_count} optional)")

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(cmd_template())
