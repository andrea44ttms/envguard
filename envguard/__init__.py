"""envguard — Lightweight .env validation and auditing utility."""

from .schema import EnvSchema, EnvVarSchema, EnvVarType
from .validator import EnvValidator
from .result import ValidationError, ValidationResult

__all__ = [
    "EnvSchema",
    "EnvVarSchema",
    "EnvVarType",
    "EnvValidator",
    "ValidationError",
    "ValidationResult",
]

__version__ = "0.1.0"
