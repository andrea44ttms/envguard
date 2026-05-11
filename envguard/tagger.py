"""Tag env variables with custom labels and filter by tag."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Iterable, List, Optional, Set

from envguard.schema import EnvSchema


@dataclass
class TagIndex:
    """Mapping of tag -> set of variable names."""

    _index: Dict[str, Set[str]] = field(default_factory=dict)

    def all_tags(self) -> List[str]:
        """Return sorted list of all known tags."""
        return sorted(self._index.keys())

    def vars_for_tag(self, tag: str) -> FrozenSet[str]:
        """Return variable names associated with *tag*."""
        return frozenset(self._index.get(tag, set()))

    def tags_for_var(self, name: str) -> FrozenSet[str]:
        """Return tags associated with *name*."""
        return frozenset(t for t, names in self._index.items() if name in names)

    def filter_env(
        self, env: Dict[str, str], tags: Iterable[str]
    ) -> Dict[str, str]:
        """Return subset of *env* whose keys carry at least one of *tags*."""
        wanted: Set[str] = set()
        for tag in tags:
            wanted |= self.vars_for_tag(tag)
        return {k: v for k, v in env.items() if k in wanted}

    def __str__(self) -> str:  # pragma: no cover
        lines = ["TagIndex:"]
        for tag in self.all_tags():
            names = ", ".join(sorted(self.vars_for_tag(tag)))
            lines.append(f"  [{tag}] {names}")
        return "\n".join(lines)


def build_tag_index(schema: EnvSchema) -> TagIndex:
    """Build a :class:`TagIndex` from the tags declared in *schema*.

    Each :class:`EnvVarSchema` may carry an optional ``tags`` attribute
    (an iterable of strings).  Variables without tags are simply omitted
    from the index.
    """
    index: Dict[str, Set[str]] = {}
    for name, var in schema.vars.items():
        tags: Optional[Iterable[str]] = getattr(var, "tags", None)
        if not tags:
            continue
        for tag in tags:
            index.setdefault(tag, set()).add(name)
    return TagIndex(_index=index)
