"""Core validation logic for envguard."""

import re
from typing import Any

from .schema import EnvSchema, EnvVarSchema, EnvVarType
from .result import ValidationResult, ValidationError


URL_PATTERN = re.compile(
    r"^(https?|ftp)://[^\s/$.?#].[^\s]*$", re.IGNORECASE
)
EMAIL_PATTERN = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.-]+$")


class EnvValidator:
    """Validates a dict of env vars against a defined EnvSchema."""

    def __init__(self, schema: EnvSchema):
        self.schema = schema

    def validate(self, env: dict[str, str]) -> ValidationResult:
        errors: list[ValidationError] = []

        for var_schema in self.schema.variables:
            raw_value = env.get(var_schema.name)

            if raw_value is None or raw_value == "":
                if var_schema.required:
                    errors.append(ValidationError(
                        var_schema.name, "Required variable is missing or empty."
                    ))
                continue

            cast_value, cast_error = self._cast(var_schema, raw_value)
            if cast_error:
                errors.append(ValidationError(var_schema.name, cast_error))
                continue

            type_errors = self._validate_constraints(var_schema, raw_value, cast_value)
            errors.extend(type_errors)

        return ValidationResult(errors=errors)

    def _cast(self, schema: EnvVarSchema, value: str) -> tuple[Any, Optional[str]]:
        try:
            if schema.var_type == EnvVarType.INTEGER:
                return int(value), None
            if schema.var_type == EnvVarType.FLOAT:
                return float(value), None
            if schema.var_type == EnvVarType.BOOLEAN:
                if value.lower() not in ("true", "false", "1", "0"):
                    return None, f"Expected boolean, got '{value}'."
                return value.lower() in ("true", "1"), None
            return value, None
        except (ValueError, TypeError):
            return None, f"Cannot cast '{value}' to {schema.var_type.value}."

    def _validate_constraints(
        self, schema: EnvVarSchema, raw: str, value: Any
    ) -> list[ValidationError]:
        errs = []
        name = schema.name

        if schema.var_type == EnvVarType.URL and not URL_PATTERN.match(raw):
            errs.append(ValidationError(name, f"'{raw}' is not a valid URL."))

        if schema.var_type == EnvVarType.EMAIL and not EMAIL_PATTERN.match(raw):
            errs.append(ValidationError(name, f"'{raw}' is not a valid email."))

        if schema.allowed_values and value not in schema.allowed_values:
            errs.append(ValidationError(
                name, f"Value '{value}' not in allowed values {schema.allowed_values}."
            ))

        if schema.min_length is not None and len(raw) < schema.min_length:
            errs.append(ValidationError(
                name, f"Value too short (min {schema.min_length} chars)."
            ))

        if schema.max_length is not None and len(raw) > schema.max_length:
            errs.append(ValidationError(
                name, f"Value too long (max {schema.max_length} chars)."
            ))

        return errs


from typing import Optional  # noqa: E402 — moved to avoid circular at top
