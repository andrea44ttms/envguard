"""Tests for envguard.reporter module."""

import json
import pytest

from envguard.result import ValidationError, ValidationResult
from envguard.reporter import ReportFormat, render_report


def _make_result(errors=None):
    errs = [ValidationError(var=e[0], message=e[1]) for e in (errors or [])]
    return ValidationResult(errors=errs)


def test_text_report_valid():
    result = _make_result()
    output = render_report(result, ReportFormat.TEXT)
    assert "passed" in output.lower()
    assert "✅" in output


def test_text_report_invalid():
    result = _make_result([("PORT", "must be integer")])
    output = render_report(result, ReportFormat.TEXT)
    assert "❌" in output
    assert "PORT" in output
    assert "must be integer" in output


def test_json_report_structure():
    result = _make_result([("HOST", "missing required variable")])
    output = render_report(result, ReportFormat.JSON)
    data = json.loads(output)
    assert data["valid"] is False
    assert data["error_count"] == 1
    assert len(data["errors"]) == 1


def test_json_report_valid():
    result = _make_result()
    data = json.loads(render_report(result, ReportFormat.JSON))
    assert data["valid"] is True
    assert data["error_count"] == 0


def test_markdown_report_contains_header():
    result = _make_result()
    output = render_report(result, ReportFormat.MARKDOWN)
    assert "## envguard Validation Report" in output


def test_markdown_report_lists_errors():
    result = _make_result([("DB_URL", "invalid format")])
    output = render_report(result, ReportFormat.MARKDOWN)
    assert "DB_URL" in output
    assert "### Errors" in output


def test_unsupported_format_raises():
    result = _make_result()
    with pytest.raises(ValueError, match="Unsupported"):
        render_report(result, "xml")  # type: ignore[arg-type]
