"""Classify env vars into semantic categories based on key patterns."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

# Pattern → category mapping (checked in order)
_RULES: List[tuple[str, str]] = [
    ("DATABASE_URL", "database"),
    ("DB_", "database"),
    ("POSTGRES", "database"),
    ("MYSQL", "database"),
    ("REDIS", "cache"),
    ("CACHE", "cache"),
    ("SECRET", "security"),
    ("PASSWORD", "security"),
    ("TOKEN", "security"),
    ("API_KEY", "security"),
    ("AUTH", "security"),
    ("LOG", "observability"),
    ("SENTRY", "observability"),
    ("METRICS", "observability"),
    ("TRACE", "observability"),
    ("PORT", "networking"),
    ("HOST", "networking"),
    ("URL", "networking"),
    ("ADDR", "networking"),
    ("DEBUG", "runtime"),
    ("ENV", "runtime"),
    ("ENVIRONMENT", "runtime"),
    ("APP_", "runtime"),
]

_UNCATEGORIZED = "uncategorized"


def _classify_key(key: str) -> str:
    upper = key.upper()
    for pattern, category in _RULES:
        if pattern in upper:
            return category
    return _UNCATEGORIZED


@dataclass
class ClassificationResult:
    categories: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def category_names(self) -> List[str]:
        return sorted(self.categories.keys())

    def vars_for(self, category: str) -> List[str]:
        return self.categories.get(category, [])

    def category_of(self, key: str) -> str:
        for cat, keys in self.categories.items():
            if key in keys:
                return cat
        return _UNCATEGORIZED

    def __str__(self) -> str:
        lines = []
        for cat in self.category_names:
            keys = ", ".join(self.categories[cat])
            lines.append(f"  [{cat}] {keys}")
        return "ClassificationResult:\n" + "\n".join(lines)


def classify_env(env: Dict[str, str]) -> ClassificationResult:
    """Classify each key in *env* into a semantic category."""
    buckets: Dict[str, List[str]] = {}
    for key in env:
        cat = _classify_key(key)
        buckets.setdefault(cat, []).append(key)
    # Sort keys within each bucket for determinism
    for cat in buckets:
        buckets[cat].sort()
    return ClassificationResult(categories=buckets)
