"""Reporting utilities for envguard validation results."""

from __future__ import annotations

import json
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from envguard.result import ValidationResult


class ReportFormat(str, Enum):
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"


def _render_text(result: "ValidationResult") -> str:
    lines = []
    if result.is_valid:
        lines.append("✅ envguard: All environment variables passed validation.")
    else:
        lines.append(f"❌ envguard: Validation failed with {result.error_count} error(s).")
        for err in result.errors:
            lines.append(f"  - {err}")
    return "\n".join(lines)


def _render_json(result: "ValidationResult") -> str:
    payload = {
        "valid": result.is_valid,
        "error_count": result.error_count,
        "errors": [str(e) for e in result.errors],
    }
    return json.dumps(payload, indent=2)


def _render_markdown(result: "ValidationResult") -> str:
    lines = ["## envguard Validation Report", ""]
    status = "✅ Passed" if result.is_valid else f"❌ Failed ({result.error_count} error(s))"
    lines.append(f"**Status:** {status}")
    if not result.is_valid:
        lines.append("")
        lines.append("### Errors")
        for err in result.errors:
            lines.append(f"- `{err}`")
    return "\n".join(lines)


_RENDERERS = {
    ReportFormat.TEXT: _render_text,
    ReportFormat.JSON: _render_json,
    ReportFormat.MARKDOWN: _render_markdown,
}


def render_report(result: "ValidationResult", fmt: ReportFormat = ReportFormat.TEXT) -> str:
    """Render a validation result in the specified format."""
    renderer = _RENDERERS.get(fmt)
    if renderer is None:
        raise ValueError(f"Unsupported report format: {fmt}")
    return renderer(result)
