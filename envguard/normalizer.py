"""Normalize raw env dicts: strip whitespace, optionally uppercase keys, filter empties."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class NormalizeOptions:
    """Options controlling normalization behaviour."""
    uppercase_keys: bool = True
    strip_values: bool = True
    strip_keys: bool = True
    drop_empty_values: bool = False
    key_prefix: Optional[str] = None  # if set, only keep keys with this prefix (after casing)


@dataclass
class NormalizeResult:
    """Outcome of a normalization pass."""
    env: Dict[str, str]
    dropped_keys: list = field(default_factory=list)
    renamed_keys: Dict[str, str] = field(default_factory=dict)  # original -> normalized

    @property
    def change_count(self) -> int:
        return len(self.dropped_keys) + len(self.renamed_keys)

    def __str__(self) -> str:  # pragma: no cover
        lines = [f"NormalizeResult: {len(self.env)} vars kept, {self.change_count} change(s)"]
        for orig, norm in self.renamed_keys.items():
            lines.append(f"  renamed: {orig!r} -> {norm!r}")
        for k in self.dropped_keys:
            lines.append(f"  dropped: {k!r}")
        return "\n".join(lines)


def normalize_env(
    raw: Dict[str, str],
    options: Optional[NormalizeOptions] = None,
) -> NormalizeResult:
    """Return a new dict with keys/values normalized according to *options*."""
    if options is None:
        options = NormalizeOptions()

    result: Dict[str, str] = {}
    dropped: list = []
    renamed: Dict[str, str] = {}

    for raw_key, raw_val in raw.items():
        key = raw_key.strip() if options.strip_keys else raw_key
        val = raw_val.strip() if options.strip_values else raw_val

        if options.uppercase_keys:
            normalized_key = key.upper()
        else:
            normalized_key = key

        if normalized_key != raw_key:
            renamed[raw_key] = normalized_key

        if options.drop_empty_values and val == "":
            dropped.append(normalized_key)
            continue

        if options.key_prefix is not None and not normalized_key.startswith(options.key_prefix):
            dropped.append(normalized_key)
            continue

        result[normalized_key] = val

    return NormalizeResult(env=result, dropped_keys=dropped, renamed_keys=renamed)
