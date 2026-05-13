"""Extract a subset of env vars based on keys, prefixes, or tags."""
from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import Dict, List, Optional

from envguard.schema import EnvSchema


@dataclass
class ExtractResult:
    extracted: Dict[str, str]
    skipped: Dict[str, str]
    source_count: int

    @property
    def extract_count(self) -> int:
        return len(self.extracted)

    @property
    def skip_count(self) -> int:
        return len(self.skipped)

    def __str__(self) -> str:
        lines = [
            f"Extracted {self.extract_count} / {self.source_count} vars",
            f"Skipped:  {self.skip_count}",
        ]
        if self.extracted:
            lines.append("Extracted keys:")
            for k, v in sorted(self.extracted.items()):
                lines.append(f"  {k}={v}")
        return "\n".join(lines)


def extract_env(
    env: Dict[str, str],
    *,
    keys: Optional[List[str]] = None,
    prefixes: Optional[List[str]] = None,
    patterns: Optional[List[str]] = None,
    schema: Optional[EnvSchema] = None,
    tags: Optional[List[str]] = None,
) -> ExtractResult:
    """Return a filtered subset of *env* according to the supplied selectors.

    Selectors are OR-combined: a key is included if it matches ANY selector.
    If no selectors are given and a schema is provided, only declared keys are
    returned.  If neither selectors nor schema are given, all keys are returned.
    """
    selected: Dict[str, str] = {}
    skipped: Dict[str, str] = {}

    tag_keys: set[str] = set()
    if tags and schema:
        for var_name, var_schema in schema.vars.items():
            if any(t in (var_schema.tags or []) for t in tags):
                tag_keys.add(var_name)

    schema_keys = set(schema.vars.keys()) if schema else None

    for k, v in env.items():
        matched = False

        if keys and k in keys:
            matched = True
        if not matched and prefixes:
            matched = any(k.startswith(p) for p in prefixes)
        if not matched and patterns:
            matched = any(fnmatch(k, p) for p in patterns)
        if not matched and tag_keys and k in tag_keys:
            matched = True
        if not matched and not keys and not prefixes and not patterns and not tags:
            matched = (schema_keys is None) or (k in schema_keys)

        if matched:
            selected[k] = v
        else:
            skipped[k] = v

    return ExtractResult(
        extracted=selected,
        skipped=skipped,
        source_count=len(env),
    )
