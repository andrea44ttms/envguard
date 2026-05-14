"""Tests for envguard.rotator."""
import pytest

from envguard.rotator import RotationCandidate, RotationReport, rotate_env


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def clean_env():
    return {
        "APP_NAME": "myapp",
        "PORT": "8080",
        "DEBUG": "false",
    }


@pytest.fixture()
def sensitive_env():
    return {
        "DB_PASSWORD": "supersecret",
        "API_KEY": "CHANGEME",
        "SECRET_TOKEN": "",
        "APP_NAME": "myapp",
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_clean_env_has_no_candidates(clean_env):
    report = rotate_env(clean_env)
    assert not report.has_candidates()
    assert report.count == 0


def test_placeholder_detected(sensitive_env):
    report = rotate_env(sensitive_env)
    keys = [c.key for c in report.candidates]
    assert "API_KEY" in keys


def test_empty_sensitive_detected(sensitive_env):
    report = rotate_env(sensitive_env)
    keys = [c.key for c in report.candidates]
    assert "SECRET_TOKEN" in keys


def test_non_empty_sensitive_not_flagged(sensitive_env):
    report = rotate_env(sensitive_env)
    keys = [c.key for c in report.candidates]
    assert "DB_PASSWORD" not in keys


def test_custom_reason_flags_key(clean_env):
    report = rotate_env(clean_env, custom_reasons={"APP_NAME": "scheduled rotation"})
    keys = [c.key for c in report.candidates]
    assert "APP_NAME" in keys
    candidate = next(c for c in report.candidates if c.key == "APP_NAME")
    assert "scheduled rotation" in candidate.reason


def test_sensitive_count(sensitive_env):
    report = rotate_env(sensitive_env)
    assert report.sensitive_count >= 1


def test_disable_empty_sensitive_check():
    env = {"SECRET_TOKEN": ""}
    report = rotate_env(env, empty_sensitive=False)
    assert not report.has_candidates()


def test_custom_placeholder_pattern():
    env = {"MY_KEY": "TODO_FILL"}
    report = rotate_env(env, placeholder_pattern="TODO_FILL")
    keys = [c.key for c in report.candidates]
    assert "MY_KEY" in keys


def test_report_str_with_candidates(sensitive_env):
    report = rotate_env(sensitive_env)
    text = str(report)
    assert "RotationReport" in text
    assert "candidate" in text


def test_report_str_no_candidates(clean_env):
    report = rotate_env(clean_env)
    text = str(report)
    assert "no rotation candidates" in text


def test_candidate_str_format():
    c = RotationCandidate(key="API_KEY", reason="placeholder", sensitive=True)
    assert "[sensitive]" in str(c)
    assert "API_KEY" in str(c)
