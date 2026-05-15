"""Compute and compare deterministic digests (checksums) of env snapshots."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class DigestResult:
    """Holds the digest of an env mapping and comparison metadata."""

    digest: str
    algorithm: str
    key_count: int
    previous: Optional[str] = None
    _changed: bool = field(init=False, default=False)

    def __post_init__(self) -> None:
        self._changed = self.previous is not None and self.previous != self.digest

    @property
    def changed(self) -> bool:
        """True when a previous digest was supplied and differs from current."""
        return self._changed

    def __str__(self) -> str:
        lines = [
            f"algorithm : {self.algorithm}",
            f"digest    : {self.digest}",
            f"keys      : {self.key_count}",
        ]
        if self.previous is not None:
            status = "CHANGED" if self._changed else "UNCHANGED"
            lines.append(f"previous  : {self.previous}")
            lines.append(f"status    : {status}")
        return "\n".join(lines)


def digest_env(
    env: Dict[str, str],
    *,
    algorithm: str = "sha256",
    previous: Optional[str] = None,
) -> DigestResult:
    """Compute a stable digest of *env*.

    Keys are sorted before hashing so insertion order does not affect the
    result.  Only ``sha256`` and ``md5`` are accepted.
    """
    if algorithm not in ("sha256", "md5"):
        raise ValueError(f"Unsupported algorithm '{algorithm}'. Use 'sha256' or 'md5'.")

    canonical = json.dumps(
        {k: env[k] for k in sorted(env)},
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode()

    h = hashlib.new(algorithm, canonical)
    return DigestResult(
        digest=h.hexdigest(),
        algorithm=algorithm,
        key_count=len(env),
        previous=previous,
    )
