"""Tests for envguard.snapshot module."""

import json
import os
import pytest

from envguard.snapshot import (
    EnvSnapshot,
    take_snapshot,
    save_snapshot,
    load_snapshot,
    diff_snapshots,
)


SAMPLE_ENV = {"APP_NAME": "myapp", "PORT": "8080", "SECRET_KEY": "hunter2"}


def test_take_snapshot_stores_values():
    snap = take_snapshot(SAMPLE_ENV)
    assert snap.values["APP_NAME"] == "myapp"
    assert snap.values["PORT"] == "8080"
    assert snap.timestamp != ""


def test_take_snapshot_is_valid_with_no_errors():
    snap = take_snapshot(SAMPLE_ENV)
    assert snap.is_valid is True
    assert snap.errors == []


def test_take_snapshot_invalid_with_errors():
    snap = take_snapshot(SAMPLE_ENV, errors=["PORT must be integer"])
    assert snap.is_valid is False
    assert len(snap.errors) == 1


def test_take_snapshot_redacts_sensitive_keys():
    snap = take_snapshot(SAMPLE_ENV, redact_keys=["SECRET_KEY"])
    assert snap.values["SECRET_KEY"] == "***"
    assert snap.values["APP_NAME"] == "myapp"


def test_take_snapshot_redact_case_insensitive():
    snap = take_snapshot(SAMPLE_ENV, redact_keys=["secret_key"])
    assert snap.values["SECRET_KEY"] == "***"


def test_snapshot_str_valid():
    snap = take_snapshot(SAMPLE_ENV)
    assert "VALID" in str(snap)
    assert "3 vars" in str(snap)


def test_snapshot_str_invalid():
    snap = take_snapshot(SAMPLE_ENV, errors=["err1", "err2"])
    assert "INVALID" in str(snap)
    assert "2 errors" in str(snap)


def test_snapshot_to_dict_structure():
    snap = take_snapshot(SAMPLE_ENV, errors=["bad"])
    d = snap.to_dict()
    assert "timestamp" in d
    assert d["is_valid"] is False
    assert d["values"] == snap.values
    assert d["errors"] == ["bad"]


def test_save_and_load_snapshot(tmp_path):
    snap = take_snapshot(SAMPLE_ENV, errors=["some error"])
    path = str(tmp_path / "snap.json")
    save_snapshot(snap, path)
    assert os.path.exists(path)
    loaded = load_snapshot(path)
    assert loaded.timestamp == snap.timestamp
    assert loaded.values == snap.values
    assert loaded.errors == snap.errors


def test_load_snapshot_missing_errors_key(tmp_path):
    path = str(tmp_path / "snap.json")
    data = {"timestamp": "2024-01-01T00:00:00+00:00", "values": {"X": "1"}}
    with open(path, "w") as fh:
        json.dump(data, fh)
    loaded = load_snapshot(path)
    assert loaded.errors == []


def test_diff_snapshots_detects_changes():
    old = take_snapshot({"A": "1", "B": "2"})
    new = take_snapshot({"A": "1", "B": "99", "C": "new"})
    changes = diff_snapshots(old, new)
    assert "B" in changes
    assert changes["B"] == {"old": "2", "new": "99"}
    assert "C" in changes
    assert changes["C"] == {"old": None, "new": "new"}
    assert "A" not in changes


def test_diff_snapshots_removed_key():
    old = take_snapshot({"A": "1", "B": "2"})
    new = take_snapshot({"A": "1"})
    changes = diff_snapshots(old, new)
    assert "B" in changes
    assert changes["B"] == {"old": "2", "new": None}


def test_diff_snapshots_no_changes():
    snap = take_snapshot(SAMPLE_ENV)
    assert diff_snapshots(snap, snap) == {}
