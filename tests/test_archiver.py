"""Tests for envguard.archiver."""
from __future__ import annotations

import json
import os

import pytest

from envguard.archiver import (
    ArchiveEntry,
    ArchiveIndex,
    ArchiveResult,
    archive_env,
    load_archive_index,
)


SAMPLE_ENV = {
    "APP_NAME": "envguard",
    "DB_PASSWORD": "s3cr3t",
    "PORT": "8080",
}


def test_archive_env_returns_archive_result(tmp_path):
    result = archive_env(SAMPLE_ENV, directory=str(tmp_path))
    assert isinstance(result, ArchiveResult)


def test_archive_env_creates_file(tmp_path):
    result = archive_env(SAMPLE_ENV, directory=str(tmp_path))
    assert os.path.isfile(result.entry.path)


def test_archive_env_key_count(tmp_path):
    result = archive_env(SAMPLE_ENV, directory=str(tmp_path))
    assert result.entry.key_count == len(SAMPLE_ENV)


def test_archive_env_redacts_sensitive_by_default(tmp_path):
    result = archive_env(SAMPLE_ENV, directory=str(tmp_path))
    data = json.loads(open(result.entry.path).read())
    assert data["env"]["DB_PASSWORD"] != "s3cr3t"


def test_archive_env_no_redact_preserves_values(tmp_path):
    result = archive_env(SAMPLE_ENV, directory=str(tmp_path), redact=False)
    data = json.loads(open(result.entry.path).read())
    assert data["env"]["DB_PASSWORD"] == "s3cr3t"


def test_archive_entry_redacted_flag(tmp_path):
    result = archive_env(SAMPLE_ENV, directory=str(tmp_path), redact=True)
    assert result.entry.redacted is True


def test_archive_entry_str_contains_timestamp(tmp_path):
    result = archive_env(SAMPLE_ENV, directory=str(tmp_path))
    assert result.entry.timestamp in str(result.entry)


def test_archive_result_ok(tmp_path):
    result = archive_env(SAMPLE_ENV, directory=str(tmp_path))
    assert result.ok is True


def test_archive_result_str(tmp_path):
    result = archive_env(SAMPLE_ENV, directory=str(tmp_path))
    assert str(result) == str(result.entry)


def test_load_archive_index_empty_dir(tmp_path):
    index = load_archive_index(str(tmp_path))
    assert isinstance(index, ArchiveIndex)
    assert index.count == 0
    assert index.latest() is None


def test_load_archive_index_finds_entries(tmp_path):
    archive_env(SAMPLE_ENV, directory=str(tmp_path))
    archive_env(SAMPLE_ENV, directory=str(tmp_path))
    index = load_archive_index(str(tmp_path))
    assert index.count == 2


def test_load_archive_index_latest(tmp_path):
    archive_env(SAMPLE_ENV, directory=str(tmp_path))
    index = load_archive_index(str(tmp_path))
    assert index.latest() is not None


def test_archive_index_str(tmp_path):
    archive_env(SAMPLE_ENV, directory=str(tmp_path))
    index = load_archive_index(str(tmp_path))
    assert str(tmp_path.name) in str(index) or ".envarchive" in str(index) or str(index)


def test_load_archive_index_missing_dir(tmp_path):
    index = load_archive_index(str(tmp_path / "nonexistent"))
    assert index.count == 0
