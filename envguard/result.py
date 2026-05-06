"""Validation result types for envguard."""

from dataclasses import dataclass, field


@dataclass
class ValidationError:
    """Represents a single validation failure."""

    variable: str
    message: str

    def __str__(self) -> str:
        return f"[{self.variable}] {self.message}"


@dataclass
class ValidationResult:
    """Aggregated result of a full schema validation run."""

    errors: list[ValidationError] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    @property
    def error_count(self) -> int:
        return len(self.errors)

    def summary(self) -> str:
        if self.is_valid:
            return "All environment variables are valid."
        lines = [f"Found {self.error_count} validation error(s):"]
        for err in self.errors:
            lines.append(f"  - {err}")
        return "\n".join(lines)

    def raise_if_invalid(self, exc_class: type = ValueError) -> None:
        """Raise an exception with the summary if validation failed."""
        if not self.is_valid:
            raise exc_class(self.summary())
