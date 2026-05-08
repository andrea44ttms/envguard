"""Format validated env values into typed Python objects."""

from typing import Any, Dict, Optional
from envguard.schema import EnvSchema, EnvVarType
from envguard.result import ValidationResult


class FormattedEnv:
    """Holds typed, formatted env values after validation."""

    def __init__(self, data: Dict[str, Any], schema: EnvSchema) -> None:
        self._data = data
        self._schema = schema

    def get(self, key: str, default: Any = None) -> Any:
        """Return typed value for key, or default if missing."""
        return self._data.get(key, default)

    def require(self, key: str) -> Any:
        """Return typed value for key, raising KeyError if absent."""
        if key not in self._data:
            raise KeyError(f"Required env var '{key}' not found in formatted env.")
        return self._data[key]

    def to_dict(self) -> Dict[str, Any]:
        """Return a shallow copy of all formatted values."""
        return dict(self._data)

    def __repr__(self) -> str:
        keys = list(self._data.keys())
        return f"FormattedEnv(keys={keys})"


def format_env(
    raw_env: Dict[str, str],
    schema: EnvSchema,
    result: Optional[ValidationResult] = None,
) -> FormattedEnv:
    """Cast raw string env values to their declared types.

    Only keys present in the schema are included. Keys with cast
    errors are skipped (they will already appear in ValidationResult
    if one was provided).
    """
    typed: Dict[str, Any] = {}

    for key, var_schema in schema.vars.items():
        raw = raw_env.get(key)
        if raw is None:
            if var_schema.default is not None:
                raw = var_schema.default
            else:
                continue

        try:
            if var_schema.type == EnvVarType.INTEGER:
                typed[key] = int(raw)
            elif var_schema.type == EnvVarType.FLOAT:
                typed[key] = float(raw)
            elif var_schema.type == EnvVarType.BOOLEAN:
                typed[key] = raw.lower() in ("true", "1", "yes")
            else:
                typed[key] = raw
        except (ValueError, AttributeError):
            # Leave malformed values out; validator already flagged them.
            pass

    return FormattedEnv(typed, schema)
