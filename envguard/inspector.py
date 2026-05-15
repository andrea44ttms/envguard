"""Inspect individual env vars: type inference, origin, and metadata summary."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from envguard.schema import EnvSchema, EnvVarType
from envguard.redactor import is_sensitive


@dataclass
class VarInspection:
    key: str
    raw_value: Optional[str]
    inferred_type: str
    declared_type: Optional[str]
    is_sensitive: bool
    is_declared: bool
    is_required: bool
    default_value: Optional[str]
    tags: List[str] = field(default_factory=list)

    def __str__(self) -> str:  # pragma: no cover
        lines = [
            f"Key          : {self.key}",
            f"Value        : {'***' if self.is_sensitive else self.raw_value!r}",
            f"Inferred type: {self.inferred_type}",
            f"Declared type: {self.declared_type or 'n/a'}",
            f"Declared     : {self.is_declared}",
            f"Required     : {self.is_required}",
            f"Default      : {self.default_value!r}",
            f"Sensitive    : {self.is_sensitive}",
            f"Tags         : {', '.join(self.tags) if self.tags else 'none'}",
        ]
        return "\n".join(lines)


@dataclass
class InspectionResult:
    inspections: List[VarInspection] = field(default_factory=list)

    def get(self, key: str) -> Optional[VarInspection]:
        for insp in self.inspections:
            if insp.key == key:
                return insp
        return None

    def __len__(self) -> int:
        return len(self.inspections)

    def __str__(self) -> str:  # pragma: no cover
        return "\n\n".join(str(i) for i in self.inspections)


def _infer_type(value: Optional[str]) -> str:
    if value is None:
        return "null"
    if value.lower() in ("true", "false", "1", "0", "yes", "no"):
        return "boolean"
    try:
        int(value)
        return "integer"
    except ValueError:
        pass
    try:
        float(value)
        return "float"
    except ValueError:
        pass
    return "string"


def inspect_env(
    env: Dict[str, str],
    schema: Optional[EnvSchema] = None,
) -> InspectionResult:
    """Return an InspectionResult describing each key in *env*."""
    schema_map = {}
    if schema is not None:
        schema_map = {var.name: var for var in schema.vars}

    inspections: List[VarInspection] = []
    for key, raw in env.items():
        declared = schema_map.get(key)
        inspections.append(
            VarInspection(
                key=key,
                raw_value=raw,
                inferred_type=_infer_type(raw),
                declared_type=declared.type.value if declared else None,
                is_sensitive=is_sensitive(key),
                is_declared=declared is not None,
                is_required=declared.required if declared else False,
                default_value=declared.default if declared else None,
                tags=list(declared.tags) if declared and declared.tags else [],
            )
        )
    return InspectionResult(inspections=inspections)
