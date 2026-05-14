"""Env rotation helper — detects stale keys and suggests rotation candidates."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from envguard.redactor import is_sensitive


@dataclass
class RotationCandidate:
    key: str
    reason: str
    sensitive: bool

    def __str__(self) -> str:
        tag = "[sensitive]" if self.sensitive else "[plain]"
        return f"{self.key} {tag}: {self.reason}"


@dataclass
class RotationReport:
    candidates: List[RotationCandidate] = field(default_factory=list)
    scanned_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def count(self) -> int:
        return len(self.candidates)

    @property
    def sensitive_count(self) -> int:
        return sum(1 for c in self.candidates if c.sensitive)

    def has_candidates(self) -> bool:
        return bool(self.candidates)

    def __str__(self) -> str:
        if not self.candidates:
            return "RotationReport: no rotation candidates found."
        lines = [f"RotationReport ({self.count} candidate(s)):"] + [
            f"  - {c}" for c in self.candidates
        ]
        return "\n".join(lines)


def rotate_env(
    env: Dict[str, str],
    *,
    empty_sensitive: bool = True,
    placeholder_pattern: str = "CHANGEME",
    custom_reasons: Optional[Dict[str, str]] = None,
) -> RotationReport:
    """Scan *env* and return keys that are rotation candidates.

    A key is flagged when:
    - It is sensitive and its value is empty or a known placeholder.
    - Its value literally matches *placeholder_pattern*.
    - A caller-supplied reason exists in *custom_reasons*.
    """
    custom_reasons = custom_reasons or {}
    candidates: List[RotationCandidate] = []

    for key, value in env.items():
        sensitive = is_sensitive(key)
        reasons: List[str] = []

        if key in custom_reasons:
            reasons.append(custom_reasons[key])

        if placeholder_pattern and placeholder_pattern.upper() in value.upper():
            reasons.append(f"value contains placeholder '{placeholder_pattern}'")

        if empty_sensitive and sensitive and not value.strip():
            reasons.append("sensitive key has empty value")

        if reasons:
            candidates.append(
                RotationCandidate(
                    key=key,
                    reason="; ".join(reasons),
                    sensitive=sensitive,
                )
            )

    return RotationReport(candidates=candidates)
