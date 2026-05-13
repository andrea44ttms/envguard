"""Tests for envguard.cli_renamer."""
import json
import pathlib
import pytest
from envguard.cli_renamer import main


@pytest.fixture()
def env_file(tmp_path: pathlib.Path) -> pathlib.Path:
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nDB_PORT=5432\nAPP_SECRET=s3cr3t\n")
    return p


def test_cmd_rename_returns_0_on_success(env_file, capsys):
    rc = main([str(env_file), "--rename", "DB_HOST=DATABASE_HOST"])
    assert rc == 0


def test_cmd_rename_output_contains_new_key(env_file, capsys):
    main([str(env_file), "--rename", "DB_HOST=DATABASE_HOST"])
    out = capsys.readouterr().out
    assert "DATABASE_HOST" in out


def test_cmd_rename_json_output(env_file, capsys):
    main([str(env_file), "--rename", "DB_HOST=DATABASE_HOST", "--json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "DATABASE_HOST" in data["renamed"]
    assert data["applied"]["DB_HOST"] == "DATABASE_HOST"


def test_cmd_rename_missing_file_returns_2(tmp_path, capsys):
    rc = main([str(tmp_path / "nonexistent.env"), "--rename", "A=B"])
    assert rc == 2


def test_cmd_rename_skipped_key_in_output(env_file, capsys):
    main([str(env_file), "--rename", "GHOST=PHANTOM"])
    out = capsys.readouterr().out
    assert "SKIPPED" in out or "skipped" in out


def test_cmd_rename_overwrite_flag(env_file, capsys):
    # DB_PORT already exists; rename DB_HOST -> DB_PORT should be skipped without flag
    rc = main([str(env_file), "--rename", "DB_HOST=DB_PORT"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "SKIPPED" in out or "skipped" in out


def test_cmd_rename_overwrite_flag_applies(env_file, capsys):
    rc = main([str(env_file), "--rename", "DB_HOST=DB_PORT", "--overwrite", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["renamed"]["DB_PORT"] == "localhost"
