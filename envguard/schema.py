"""Schema definition models for envguard validation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class EnvVarType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    URL = "url"
    EMAIL = "email"


@dataclass
class EnvVarSchema:
    """Defines the expected schema for a single environment variable."""

    name: str
    required: bool = True
    var_type: EnvVarType = EnvVarType.STRING
    default: Optional[Any] = None
    allowed_values: Optional[list] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    description: str = ""

    def __post_init__(self):
        if self.default is not None and self.required:
            self.required = False


@dataclass
class EnvSchema:
    """Collection of EnvVarSchema definitions representing the full schema."""

    variables: list[EnvVarSchema] = field(default_factory=list)

    def add(self, var: EnvVarSchema) -> None:
        self.variables.append(var)

    def get(self, name: str) -> Optional[EnvVarSchema]:
        return next((v for v in self.variables if v.name == name), None)

    def required_vars(self) -> list[EnvVarSchema]:
        return [v for v in self.variables if v.required]

    def optional_vars(self) -> list[EnvVarSchema]:
        return [v for v in self.variables if not v.required]
