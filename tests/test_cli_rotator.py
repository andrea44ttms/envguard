"""Tests for envguard.cli_rotator."""
import json
from pathlib import Path

import pytest

from envguard.cli_rotator import cmd_rotate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_file(tmp_path: Path):
    def _write(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(content)
        return p

    return _write


def _args(
    path,
    placeholder="CHANGEME",
    no_empty_check=False,
    reason=None,
    fmt="text",
):
    class A:
        env_file = str(path)
        placeholder = placeholder  # noqa: F841
        no_empty_check = no_empty_check  # noqa: F841
        format = fmt  # noqa: F841
        reason = reason  # noqa: F841

    return A()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_clean_env_returns_0(env_file):
    p = env_file("APP_NAME=myapp\nPORT=8080\n")
    assert cmd_rotate(_args(p)) == 0


def test_placeholder_returns_1(env_file):
    p = env_file("API_KEY=CHANGEME\n")
    assert cmd_rotate(_args(p)) == 1


def test_empty_sensitive_returns_1(env_file):
    p = env_file("SECRET_TOKEN=\n")
    assert cmd_rotate(_args(p)) == 1


def test_no_empty_check_flag(env_file):
    p = env_file("SECRET_TOKEN=\n")
    assert cmd_rotate(_args(p, no_empty_check=True)) == 0


def test_json_output_structure(env_file, capsys):
    p = env_file("API_KEY=CHANGEME\n")
    cmd_rotate(_args(p, fmt="json"))
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "candidates" in data
    assert "count" in data
    assert data["count"] >= 1


def test_missing_file_returns_2(tmp_path):
    p = tmp_path / "missing.env"
    assert cmd_rotate(_args(p)) == 2


def test_custom_reason_flags_key(env_file):
    p = env_file("APP_NAME=myapp\n")
    assert cmd_rotate(_args(p, reason=["APP_NAME=scheduled rotation"])) == 1
