"""Variable interpolation for .env values.

Supports ${VAR} and $VAR syntax, resolving references from a given
environment mapping (e.g. already-loaded env vars or os.environ).
"""

import re
from typing import Dict, Optional

_PATTERN = re.compile(r"\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


class InterpolationError(Exception):
    """Raised when a referenced variable cannot be resolved."""

    def __init__(self, var: str, referencing_key: str) -> None:
        self.var = var
        self.referencing_key = referencing_key
        super().__init__(
            f"Variable '{referencing_key}' references undefined variable '${var}'"
        )


def interpolate(
    env: Dict[str, str],
    context: Optional[Dict[str, str]] = None,
    *,
    strict: bool = True,
) -> Dict[str, str]:
    """Resolve variable references in *env* values.

    Args:
        env: Mapping of key -> raw value (may contain ``${VAR}`` references).
        context: Additional variables available for resolution (e.g. os.environ).
                 Values in *env* take precedence over *context*.
        strict: If ``True`` (default), raise :class:`InterpolationError` for
                unresolvable references.  If ``False``, leave the placeholder
                intact.

    Returns:
        A new dict with all resolvable placeholders expanded.
    """
    lookup: Dict[str, str] = {**(context or {}), **env}
    result: Dict[str, str] = {}

    for key, raw in env.items():
        result[key] = _resolve(raw, key, lookup, strict=strict)

    return result


def _resolve(
    value: str,
    key: str,
    lookup: Dict[str, str],
    *,
    strict: bool,
) -> str:
    """Replace all placeholders in *value* using *lookup*."""

    def replacer(match: re.Match) -> str:  # type: ignore[type-arg]
        var_name = match.group(1) or match.group(2)
        if var_name in lookup:
            return lookup[var_name]
        if strict:
            raise InterpolationError(var_name, key)
        return match.group(0)  # leave placeholder intact

    return _PATTERN.sub(replacer, value)
