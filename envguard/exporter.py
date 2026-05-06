"""Export validated environment variables to various targets."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any


def export_to_os_environ(values: Dict[str, Any]) -> None:
    """Write cast/validated values back into os.environ as strings."""
    for key, value in values.items():
        os.environ[key] = str(value)


def export_to_dotenv(values: Dict[str, Any], path: str | Path = ".env.validated") -> None:
    """Write validated values to a .env-style file."""
    path = Path(path)
    lines = []
    for key, value in values.items():
        escaped = str(value).replace('"', '\\"')
        lines.append(f'{key}="{escaped}"')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_to_dict(values: Dict[str, Any]) -> Dict[str, str]:
    """Return a plain string-keyed, string-valued dictionary of the validated env."""
    return {key: str(value) for key, value in values.items()}
