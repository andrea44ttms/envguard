"""Tests for envguard.loader."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from envguard.loader import EnvFileNotFoundError, EnvParseError, load_env_file


@pytest.fixture()
def env_file(tmp_path: Path):
    """Factory fixture: write content to a temp .env file and return its path."""

    def _write(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(textwrap.dedent(content), encoding="utf-8")
        return p

    return _write


def test_simple_key_value(env_file):
    path = env_file("""
        APP_NAME=envguard
        DEBUG=true
    """)
    result = load_env_file(path)
    assert result == {"APP_NAME": "envguard", "DEBUG": "true"}


def test_ignores_blank_lines_and_comments(env_file):
    path = env_file("""
        # This is a comment
        APP_ENV=production

        # Another comment
        PORT=8080
    """)
    result = load_env_file(path)
    assert result == {"APP_ENV": "production", "PORT": "8080"}


def test_strips_inline_comments(env_file):
    path = env_file("""
        HOST=localhost # the host
        PORT=5432
    """)
    result = load_env_file(path)
    assert result["HOST"] == "localhost"


def test_quoted_values_preserved(env_file):
    path = env_file("""
        SECRET='my secret value'
        GREETING="hello world"
    """)
    result = load_env_file(path)
    assert result["SECRET"] == "my secret value"
    assert result["GREETING"] == "hello world"


def test_export_prefix_stripped(env_file):
    path = env_file("""
        export DATABASE_URL=postgres://localhost/db
    """)
    result = load_env_file(path)
    assert result == {"DATABASE_URL": "postgres://localhost/db"}


def test_file_not_found_raises(tmp_path):
    with pytest.raises(EnvFileNotFoundError):
        load_env_file(tmp_path / "nonexistent.env")


def test_malformed_line_raises(env_file):
    path = env_file("""
        THIS IS NOT VALID
    """)
    with pytest.raises(EnvParseError):
        load_env_file(path)


def test_empty_value_allowed(env_file):
    path = env_file("""
        EMPTY=
    """)
    result = load_env_file(path)
    assert result["EMPTY"] == ""
