"""Mask env values for safe display in logs, CLI output, or reports."""

from dataclasses import dataclass, field
from typing import Dict, Optional
from envguard.redactor import is_sensitive


_DEFAULT_MASK = "***"
_PARTIAL_VISIBLE = 4  # characters revealed at start/end for partial masking


@dataclass
class MaskResult:
    original: Dict[str, str]
    masked: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.masked:
            self.masked = dict(self.original)

    @property
    def masked_count(self) -> int:
        return sum(
            1 for k in self.original if self.masked.get(k) != self.original.get(k)
        )

    def __str__(self) -> str:
        lines = [f"{k}={v}" for k, v in self.masked.items()]
        return "\n".join(lines)


def _full_mask(value: str, mask: str = _DEFAULT_MASK) -> str:
    return mask


def _partial_mask(value: str, mask: str = _DEFAULT_MASK) -> str:
    """Show first and last N chars, mask the middle."""
    if len(value) <= _PARTIAL_VISIBLE * 2:
        return mask
    return value[:_PARTIAL_VISIBLE] + mask + value[-_PARTIAL_VISIBLE:]


def mask_env(
    env: Dict[str, str],
    partial: bool = False,
    extra_keys: Optional[list] = None,
    mask: str = _DEFAULT_MASK,
) -> MaskResult:
    """Return a MaskResult with sensitive values masked.

    Args:
        env: Raw environment dict.
        partial: If True, reveal first/last chars instead of full masking.
        extra_keys: Additional key names to treat as sensitive.
        mask: The mask string to use (default '***').
    """
    extra = set(k.upper() for k in (extra_keys or []))
    masked: Dict[str, str] = {}

    for key, value in env.items():
        if is_sensitive(key) or key.upper() in extra:
            masked[key] = _partial_mask(value, mask) if partial else _full_mask(value, mask)
        else:
            masked[key] = value

    return MaskResult(original=env, masked=masked)
