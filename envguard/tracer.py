"""Trace the origin and history of env var values across multiple sources."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TraceEntry:
    source: str
    value: str
    overridden_by: Optional[str] = None

    def __str__(self) -> str:
        status = f" (overridden by '{self.overridden_by}')" if self.overridden_by else " (active)"
        return f"  [{self.source}] {self.value!r}{status}"


@dataclass
class VarTrace:
    key: str
    entries: List[TraceEntry] = field(default_factory=list)

    @property
    def active_value(self) -> Optional[str]:
        for entry in self.entries:
            if entry.overridden_by is None:
                return entry.value
        return None

    @property
    def active_source(self) -> Optional[str]:
        for entry in self.entries:
            if entry.overridden_by is None:
                return entry.source
        return None

    def __str__(self) -> str:
        lines = [f"{self.key}:"]
        lines.extend(str(e) for e in self.entries)
        return "\n".join(lines)


@dataclass
class TraceResult:
    traces: Dict[str, VarTrace] = field(default_factory=dict)

    def get(self, key: str) -> Optional[VarTrace]:
        return self.traces.get(key)

    @property
    def all_keys(self) -> List[str]:
        return sorted(self.traces.keys())

    def __str__(self) -> str:
        if not self.traces:
            return "No variables traced."
        return "\n".join(str(self.traces[k]) for k in self.all_keys)


def trace_env(
    sources: List[tuple[str, Dict[str, str]]],
) -> TraceResult:
    """Trace variable values across ordered sources (lowest to highest priority).

    Args:
        sources: List of (source_name, env_dict) tuples ordered from lowest
                 to highest priority. The last source wins for each key.
    """
    # Collect all keys
    all_keys: set[str] = set()
    for _, env in sources:
        all_keys.update(env.keys())

    result = TraceResult()

    for key in all_keys:
        trace = VarTrace(key=key)
        # Determine which source ultimately wins
        winning_source: Optional[str] = None
        for source_name, env in reversed(sources):
            if key in env:
                winning_source = source_name
                break

        for source_name, env in sources:
            if key not in env:
                continue
            overridden_by: Optional[str] = None
            if source_name != winning_source:
                # Find the next higher-priority source that has this key
                idx = [s for s, _ in sources].index(source_name)
                for higher_name, higher_env in sources[idx + 1:]:
                    if key in higher_env:
                        overridden_by = higher_name
                        break
            trace.entries.append(
                TraceEntry(source=source_name, value=env[key], overridden_by=overridden_by)
            )

        result.traces[key] = trace

    return result
