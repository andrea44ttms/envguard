"""envguard.caster — Bulk-cast raw env dicts to typed Python values."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from envguard.schema import EnvSchema, EnvVarType


@dataclass
class CastError:
    key: str
    raw: str
    expected_type: str
    reason: str

    def __str__(self) -> str:
        return (
            f"[{self.key}] cannot cast {self.raw!r} to {self.expected_type}: {self.reason}"
        )


@dataclass
class CastResult:
    values: Dict[str, Any] = field(default_factory=dict)
    errors: List[CastError] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    @property
    def error_count(self) -> int:
        return len(self.errors)

    def __str__(self) -> str:
        lines = [f"CastResult: {len(self.values)} values, {self.error_count} error(s)"]
        for err in self.errors:
            lines.append(f"  {err}")
        return "\n".join(lines)


def _cast_value(key: str, raw: str, var_type: EnvVarType) -> tuple[Any, Optional[CastError]]:
    """Attempt to cast *raw* to the requested type. Returns (value, error)."""
    try:
        if var_type == EnvVarType.STRING:
            return raw, None
        if var_type == EnvVarType.INTEGER:
            return int(raw), None
        if var_type == EnvVarType.FLOAT:
            return float(raw), None
        if var_type == EnvVarType.BOOLEAN:
            if raw.lower() in ("true", "1", "yes", "on"):
                return True, None
            if raw.lower() in ("false", "0", "no", "off"):
                return False, None
            raise ValueError(f"unrecognised boolean literal {raw!r}")
    except (ValueError, TypeError) as exc:
        return None, CastError(
            key=key,
            raw=raw,
            expected_type=var_type.value,
            reason=str(exc),
        )
    return raw, None  # fallback


def cast_env(raw_env: Dict[str, str], schema: EnvSchema) -> CastResult:
    """Cast every declared variable in *raw_env* according to *schema*.

    Keys present in *raw_env* but not declared in *schema* are passed through
    as plain strings without error.
    """
    result = CastResult()
    declared = {var.name: var for var in schema.vars}

    for key, raw in raw_env.items():
        if key not in declared:
            result.values[key] = raw
            continue
        var_type = declared[key].type
        value, error = _cast_value(key, raw, var_type)
        if error:
            result.errors.append(error)
        else:
            result.values[key] = value

    return result
