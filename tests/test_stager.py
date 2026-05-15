"""Tests for envguard.stager and envguard.cli_stager."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from envguard.stager import StageResult, stage_env
from envguard.cli_stager import cmd_stage


@pytest.fixture()
def sample_env() -> dict:
    return {
        "PROD_DB_HOST": "db.prod.example.com",
        "PROD_DB_PORT": "5432",
        "STAGING_DB_HOST": "db.staging.example.com",
        "DEV_DB_HOST": "localhost",
        "APP_NAME": "myapp",
    }


def test_stage_env_returns_stage_result(sample_env):
    result = stage_env(sample_env, "production")
    assert isinstance(result, StageResult)


def test_production_stage_matches_prod_prefix(sample_env):
    result = stage_env(sample_env, "production")
    assert "DB_HOST" in result.matched
    assert "DB_PORT" in result.matched


def test_production_excludes_staging_and_dev(sample_env):
    result = stage_env(sample_env, "production")
    assert "STAGING_DB_HOST" in result.excluded
    assert "DEV_DB_HOST" in result.excluded


def test_staging_stage_matches_staging_prefix(sample_env):
    result = stage_env(sample_env, "staging")
    assert "DB_HOST" in result.matched
    assert result.matched["DB_HOST"] == "db.staging.example.com"


def test_strip_prefix_removes_stage_prefix(sample_env):
    result = stage_env(sample_env, "production", strip_prefix=True)
    assert "DB_HOST" in result.matched
    assert "PROD_DB_HOST" not in result.matched


def test_no_strip_prefix_keeps_full_key(sample_env):
    result = stage_env(sample_env, "production", strip_prefix=False)
    assert "PROD_DB_HOST" in result.matched


def test_match_count_correct(sample_env):
    result = stage_env(sample_env, "production")
    assert result.match_count == 2


def test_excluded_count_correct(sample_env):
    result = stage_env(sample_env, "production")
    assert result.excluded_count == 3


def test_custom_stage_prefixes(sample_env):
    custom = {"myprod": ["PROD_"]}
    result = stage_env(sample_env, "myprod", stage_prefixes=custom)
    assert result.match_count == 2


def test_unknown_stage_returns_all_excluded(sample_env):
    result = stage_env(sample_env, "canary")
    assert result.match_count == 0
    assert result.excluded_count == len(sample_env)


def test_str_output_contains_stage_name(sample_env):
    result = stage_env(sample_env, "development")
    assert "development" in str(result)


# --- CLI tests ---

@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    f = tmp_path / ".env"
    f.write_text(
        "PROD_DB_HOST=db.prod.example.com\n"
        "STAGING_DB_HOST=db.staging.example.com\n"
        "APP_NAME=myapp\n"
    )
    return f


def _args(env_file, stage, **kwargs):
    import argparse
    ns = argparse.Namespace(
        env_file=str(env_file),
        stage=stage,
        prefixes=kwargs.get("prefixes"),
        no_strip=kwargs.get("no_strip", False),
        format=kwargs.get("format", "text"),
    )
    return ns


def test_cmd_stage_returns_0_on_valid_file(env_file):
    assert cmd_stage(_args(env_file, "production")) == 0


def test_cmd_stage_returns_2_on_missing_file(tmp_path):
    missing = tmp_path / "no.env"
    assert cmd_stage(_args(missing, "production")) == 2


def test_cmd_stage_json_output(env_file, capsys):
    cmd_stage(_args(env_file, "production", format="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["stage"] == "production"
    assert "matched" in data


def test_cmd_stage_dotenv_output(env_file, capsys):
    cmd_stage(_args(env_file, "production", format="dotenv"))
    out = capsys.readouterr().out
    assert "=" in out
