"""Tests for envguard.watcher."""

import os
import time
import pytest

from envguard.watcher import EnvWatcher
from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType
from envguard.result import ValidationResult


@pytest.fixture
def env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("APP_PORT=8080\n")
    return f


@pytest.fixture
def schema():
    s = EnvSchema()
    s.add(EnvVarSchema(name="APP_PORT", type=EnvVarType.INTEGER, required=True))
    return s


def test_watcher_starts_and_stops(env_file, schema):
    results = []
    watcher = EnvWatcher(str(env_file), schema, on_change=results.append, poll_interval=0.1)
    watcher.start()
    assert watcher.is_running()
    watcher.stop()
    assert not watcher.is_running()


def test_watcher_detects_file_change(env_file, schema):
    results = []

    watcher = EnvWatcher(str(env_file), schema, on_change=results.append, poll_interval=0.05)
    watcher.start()

    # Modify file after a short delay
    time.sleep(0.1)
    env_file.write_text("APP_PORT=9090\n")
    time.sleep(0.3)

    watcher.stop()

    assert len(results) >= 1
    assert isinstance(results[0], ValidationResult)
    assert results[0].is_valid


def test_watcher_reports_invalid_after_bad_change(env_file, schema):
    results = []

    watcher = EnvWatcher(str(env_file), schema, on_change=results.append, poll_interval=0.05)
    watcher.start()

    time.sleep(0.1)
    env_file.write_text("APP_PORT=not_a_number\n")
    time.sleep(0.3)

    watcher.stop()

    assert len(results) >= 1
    assert not results[-1].is_valid


def test_watcher_no_callback_when_unchanged(env_file, schema):
    results = []

    watcher = EnvWatcher(str(env_file), schema, on_change=results.append, poll_interval=0.05)
    watcher.start()
    time.sleep(0.25)
    watcher.stop()

    # File was never changed after watcher started; no callbacks expected
    assert len(results) == 0


def test_start_is_idempotent(env_file, schema):
    watcher = EnvWatcher(str(env_file), schema, on_change=lambda r: None, poll_interval=0.1)
    watcher.start()
    thread_before = watcher._thread
    watcher.start()  # second call should be a no-op
    assert watcher._thread is thread_before
    watcher.stop()
