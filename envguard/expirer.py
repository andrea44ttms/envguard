"""Expiry checker: flags env vars that have passed a defined expiry date."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List, Optional


_DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y")


def _parse_date(value: str) -> Optional[date]:
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


@dataclass
class ExpiryEntry:
    key: str
    raw_value: str
    expiry_date: date
    is_expired: bool
    days_remaining: int  # negative when expired

    def __str__(self) -> str:
        status = "EXPIRED" if self.is_expired else "ok"
        return f"{self.key}: {self.expiry_date} [{status}, {self.days_remaining}d]"


@dataclass
class ExpiryReport:
    entries: List[ExpiryEntry] = field(default_factory=list)
    unparseable: List[str] = field(default_factory=list)

    @property
    def expired_count(self) -> int:
        return sum(1 for e in self.entries if e.is_expired)

    @property
    def has_expired(self) -> bool:
        return self.expired_count > 0

    def __str__(self) -> str:
        lines = ["Expiry Report"]
        for entry in self.entries:
            lines.append(f"  {entry}")
        if self.unparseable:
            lines.append("  Unparseable keys: " + ", ".join(self.unparseable))
        lines.append(f"  Expired: {self.expired_count}/{len(self.entries)}")
        return "\n".join(lines)


def check_expiry(
    env: Dict[str, str],
    expiry_keys: List[str],
    reference_date: Optional[date] = None,
) -> ExpiryReport:
    """Check whether date-valued keys in *env* have expired.

    Args:
        env: Mapping of environment variable names to string values.
        expiry_keys: Keys whose values should be interpreted as dates.
        reference_date: Date to compare against (defaults to today).

    Returns:
        An :class:`ExpiryReport` summarising the findings.
    """
    today = reference_date or date.today()
    report = ExpiryReport()

    for key in expiry_keys:
        raw = env.get(key, "")
        parsed = _parse_date(raw)
        if parsed is None:
            report.unparseable.append(key)
            continue
        delta = (parsed - today).days
        report.entries.append(
            ExpiryEntry(
                key=key,
                raw_value=raw,
                expiry_date=parsed,
                is_expired=delta < 0,
                days_remaining=delta,
            )
        )

    return report
