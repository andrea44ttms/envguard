"""Redaction utilities for masking sensitive environment variable values."""

from __future__ import annotations

from typing import Dict, Iterable, Optional

# Keys containing any of these substrings (case-insensitive) are considered sensitive.
_SENSITIVE_KEYWORDS: tuple[str, ...] = (
    "secret",
    "password",
    "passwd",
    "token",
    "api_key",
    "apikey",
    "private",
    "credential",
    "auth",
)

_REDACTED_PLACEHOLDER = "***REDACTED***"


def is_sensitive(key: str, extra_keywords: Optional[Iterable[str]] = None) -> bool:
    """Return True if *key* looks like it holds sensitive data."""
    normalised = key.lower()
    keywords = _SENSITIVE_KEYWORDS
    if extra_keywords:
        keywords = keywords + tuple(k.lower() for k in extra_keywords)
    return any(kw in normalised for kw in keywords)


def redact_value(
    key: str,
    value: str,
    extra_keywords: Optional[Iterable[str]] = None,
    placeholder: str = _REDACTED_PLACEHOLDER,
) -> str:
    """Return *placeholder* when *key* is sensitive, otherwise return *value* unchanged."""
    if is_sensitive(key, extra_keywords):
        return placeholder
    return value


def redact_env(
    env: Dict[str, str],
    extra_keywords: Optional[Iterable[str]] = None,
    placeholder: str = _REDACTED_PLACEHOLDER,
) -> Dict[str, str]:
    """Return a copy of *env* with sensitive values replaced by *placeholder*."""
    return {
        key: redact_value(key, value, extra_keywords, placeholder)
        for key, value in env.items()
    }


def redact_dict(
    data: Dict[str, str],
    sensitive_keys: Iterable[str],
    placeholder: str = _REDACTED_PLACEHOLDER,
) -> Dict[str, str]:
    """Return a copy of *data* with explicitly listed *sensitive_keys* redacted.

    Unlike :func:`redact_env`, this variant uses an explicit allow-list of keys
    rather than heuristic keyword matching.
    """
    sensitive_set = {k.lower() for k in sensitive_keys}
    return {
        key: (placeholder if key.lower() in sensitive_set else value)
        for key, value in data.items()
    }
