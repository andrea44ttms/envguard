"""Split an env dict into multiple named buckets based on prefix or explicit mapping."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SplitResult:
    """Result of splitting an env dict into named buckets."""

    buckets: Dict[str, Dict[str, str]] = field(default_factory=dict)
    unmatched: Dict[str, str] = field(default_factory=dict)

    # ------------------------------------------------------------------ #
    @property
    def bucket_names(self) -> List[str]:
        return list(self.buckets.keys())

    @property
    def total_matched(self) -> int:
        return sum(len(v) for v in self.buckets.values())

    @property
    def unmatched_count(self) -> int:
        return len(self.unmatched)

    def get(self, name: str) -> Dict[str, str]:
        """Return the bucket for *name*, or an empty dict if absent."""
        return self.buckets.get(name, {})

    def __str__(self) -> str:  # pragma: no cover
        lines = [f"SplitResult: {len(self.buckets)} bucket(s), {self.unmatched_count} unmatched"]
        for name, items in self.buckets.items():
            lines.append(f"  [{name}] {len(items)} key(s)")
        if self.unmatched:
            lines.append(f"  [unmatched] {list(self.unmatched.keys())}")
        return "\n".join(lines)


def split_env(
    env: Dict[str, str],
    prefixes: Optional[List[str]] = None,
    mapping: Optional[Dict[str, str]] = None,
    strip_prefix: bool = True,
) -> SplitResult:
    """Split *env* into buckets.

    Parameters
    ----------
    env:
        Source environment dictionary.
    prefixes:
        List of prefix strings.  Each key whose name starts with a prefix is
        placed in the bucket named after that prefix.  When multiple prefixes
        match, the longest one wins.
    mapping:
        Explicit ``{key: bucket_name}`` assignments.  Takes precedence over
        prefix matching.
    strip_prefix:
        When *True* (default) the matched prefix is removed from the key
        stored in the bucket.
    """
    prefixes = prefixes or []
    mapping = mapping or {}

    buckets: Dict[str, Dict[str, str]] = {}
    unmatched: Dict[str, str] = {}

    for key, value in env.items():
        # Explicit mapping wins.
        if key in mapping:
            bucket = mapping[key]
            buckets.setdefault(bucket, {})[key] = value
            continue

        # Find the longest matching prefix.
        matched_prefix: Optional[str] = None
        for pfx in sorted(prefixes, key=len, reverse=True):
            if key.startswith(pfx):
                matched_prefix = pfx
                break

        if matched_prefix is not None:
            bucket_key = key[len(matched_prefix):] if strip_prefix else key
            buckets.setdefault(matched_prefix, {})[bucket_key] = value
        else:
            unmatched[key] = value

    return SplitResult(buckets=buckets, unmatched=unmatched)
