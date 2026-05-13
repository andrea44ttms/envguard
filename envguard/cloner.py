"""Clone an env dict by selectively copying keys based on a pattern or key list."""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CloneResult:
    """Result of a clone operation."""

    cloned: Dict[str, str]
    skipped: List[str]
    source_size: int

    @property
    def clone_count(self) -> int:
        return len(self.cloned)

    @property
    def skip_count(self) -> int:
        return len(self.skipped)

    def __str__(self) -> str:
        lines = [
            f"CloneResult: {self.clone_count} cloned, {self.skip_count} skipped",
            f"  Source size : {self.source_size}",
            f"  Cloned keys : {', '.join(sorted(self.cloned)) or '(none)'}",
            f"  Skipped keys: {', '.join(sorted(self.skipped)) or '(none)'}",
        ]
        return "\n".join(lines)


def clone_env(
    env: Dict[str, str],
    *,
    keys: Optional[List[str]] = None,
    pattern: Optional[str] = None,
    prefix: Optional[str] = None,
    strip_prefix: bool = False,
) -> CloneResult:
    """Return a filtered copy of *env*.

    Priority of selectors: *keys* > *pattern* > *prefix*.
    If none are given, all keys are cloned.

    Args:
        env: Source environment mapping.
        keys: Explicit list of keys to include.
        pattern: Glob pattern matched against each key (e.g. ``"DB_*"``).
        prefix: Include only keys that start with this prefix.
        strip_prefix: When *prefix* is given, remove the prefix from cloned keys.
    """
    cloned: Dict[str, str] = {}
    skipped: List[str] = []

    for key, value in env.items():
        selected = False

        if keys is not None:
            selected = key in keys
        elif pattern is not None:
            selected = fnmatch.fnmatch(key, pattern)
        elif prefix is not None:
            selected = key.startswith(prefix)
        else:
            selected = True

        if selected:
            out_key = key
            if strip_prefix and prefix and key.startswith(prefix):
                out_key = key[len(prefix):]
            cloned[out_key] = value
        else:
            skipped.append(key)

    return CloneResult(cloned=cloned, skipped=skipped, source_size=len(env))
