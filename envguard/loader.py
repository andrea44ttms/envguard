"""Loader module for parsing .env files into a dictionary."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, Optional


class EnvFileNotFoundError(FileNotFoundError):
    """Raised when the specified .env file does not exist."""


class EnvParseError(ValueError):
    """Raised when a line in the .env file cannot be parsed."""


_LINE_RE = re.compile(
    r"^\s*(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.*)\s*$"
)
_QUOTED_RE = re.compile(r'^([\'"])(?P<inner>.*)\1$', re.DOTALL)


def _strip_inline_comment(value: str) -> str:
    """Remove unquoted inline comments (# ...) from a value string."""
    # Only strip if value is not quoted
    match = _QUOTED_RE.match(value)
    if match:
        return match.group("inner")
    # Strip inline comment
    comment_pos = value.find(" #")
    if comment_pos != -1:
        value = value[:comment_pos]
    return value.strip()


def load_env_file(
    path: str | Path = ".env",
    override: bool = False,
    encoding: str = "utf-8",
) -> Dict[str, str]:
    """Parse a .env file and return a dict of key/value pairs.

    Args:
        path: Path to the .env file.
        override: If True, existing ``os.environ`` values are overridden when
                  the caller later exports the result. (Does not modify
                  ``os.environ`` itself; that is left to the exporter.)
        encoding: File encoding to use.

    Returns:
        Dictionary mapping variable names to their string values.

    Raises:
        EnvFileNotFoundError: If *path* does not exist.
        EnvParseError: If a non-comment, non-blank line cannot be parsed.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise EnvFileNotFoundError(f".env file not found: {file_path}")

    env: Dict[str, str] = {}

    with file_path.open(encoding=encoding) as fh:
        for lineno, raw_line in enumerate(fh, start=1):
            line = raw_line.strip()
            # Skip blank lines and comments
            if not line or line.startswith("#"):
                continue
            # Strip optional 'export ' prefix
            if line.startswith("export "):
                line = line[len("export "):].lstrip()
            match = _LINE_RE.match(line)
            if not match:
                raise EnvParseError(
                    f"Cannot parse line {lineno} in {file_path!r}: {raw_line!r}"
                )
            key = match.group("key")
            raw_value = match.group("value")
            value = _strip_inline_comment(raw_value)
            env[key] = value

    return env
