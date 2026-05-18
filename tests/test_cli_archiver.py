"""Tests for envguard.cli_archiver."""
from __future__ import annotations

import argparse
import json
import os

import pytest

from envguard.cli_archiver import cmd_archive


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("APP_NAME=envguard\nDB_PASSWORD=s3cr3t\nPORT=8080\n")
    return str(p)


def _args(**kwargs):
    defaults = {"command": "save", "dir": None, "no_redact": False, "prefix": "envguard"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_archive_save_returns_0(tmp_path, env_file):
    args = _args(command="save", env_file=env_file, dir=str(tmp_path / "arch"))
    assert cmd_archive(args) == 0


def test_cmd_archive_save_creates_file(tmp_path, env_file):
    arch_dir = str(tmp_path / "arch")
    args = _args(command="save", env_file=env_file, dir=arch_dir)
    cmd_archive(args)
    files = os.listdir(arch_dir)
    assert len(files) == 1
    assert files[0].endswith(".json")


def test_cmd_archive_save_missing_file_returns_2(tmp_path):
    args = _args(command="save", env_file="/no/such/file.env", dir=str(tmp_path / "arch"))
    assert cmd_archive(args) == 2


def test_cmd_archive_list_returns_0(tmp_path, env_file):
    arch_dir = str(tmp_path / "arch")
    save_args = _args(command="save", env_file=env_file, dir=arch_dir)
    cmd_archive(save_args)
    list_args = argparse.Namespace(command="list", dir=arch_dir)
    assert cmd_archive(list_args) == 0


def test_cmd_archive_list_empty_dir_returns_0(tmp_path):
    args = argparse.Namespace(command="list", dir=str(tmp_path / "empty"))
    assert cmd_archive(args) == 0


def test_cmd_archive_no_redact_stores_plain_value(tmp_path, env_file):
    arch_dir = str(tmp_path / "arch")
    args = _args(command="save", env_file=env_file, dir=arch_dir, no_redact=True)
    cmd_archive(args)
    fname = os.listdir(arch_dir)[0]
    data = json.loads(open(os.path.join(arch_dir, fname)).read())
    assert data["env"]["DB_PASSWORD"] == "s3cr3t"
