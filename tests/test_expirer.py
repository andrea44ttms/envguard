"""Tests for envguard.expirer."""
from datetime import date

import pytest

from envguard.expirer import ExpiryEntry, ExpiryReport, check_expiry


REF = date(2024, 6, 15)


@pytest.fixture()
def env():
    return {
        "CERT_EXPIRY": "2024-01-01",  # expired
        "TOKEN_EXPIRY": "2025-12-31",  # valid
        "API_KEY_EXPIRY": "2024-06-15",  # exactly today (not expired)
        "BAD_DATE": "not-a-date",
    }


def test_expired_key_detected(env):
    report = check_expiry(env, ["CERT_EXPIRY"], reference_date=REF)
    assert report.expired_count == 1
    assert report.has_expired


def test_future_key_not_expired(env):
    report = check_expiry(env, ["TOKEN_EXPIRY"], reference_date=REF)
    assert report.expired_count == 0
    assert not report.has_expired


def test_same_day_not_expired(env):
    report = check_expiry(env, ["API_KEY_EXPIRY"], reference_date=REF)
    entry = report.entries[0]
    assert not entry.is_expired
    assert entry.days_remaining == 0


def test_days_remaining_negative_when_expired(env):
    report = check_expiry(env, ["CERT_EXPIRY"], reference_date=REF)
    entry = report.entries[0]
    assert entry.days_remaining < 0


def test_unparseable_key_recorded(env):
    report = check_expiry(env, ["BAD_DATE"], reference_date=REF)
    assert "BAD_DATE" in report.unparseable
    assert len(report.entries) == 0


def test_missing_key_treated_as_unparseable(env):
    report = check_expiry(env, ["NONEXISTENT"], reference_date=REF)
    assert "NONEXISTENT" in report.unparseable


def test_multiple_keys_mixed_results(env):
    report = check_expiry(
        env, ["CERT_EXPIRY", "TOKEN_EXPIRY", "BAD_DATE"], reference_date=REF
    )
    assert len(report.entries) == 2
    assert len(report.unparseable) == 1
    assert report.expired_count == 1


def test_str_output_contains_key(env):
    report = check_expiry(env, ["CERT_EXPIRY"], reference_date=REF)
    text = str(report)
    assert "CERT_EXPIRY" in text
    assert "EXPIRED" in text


def test_entry_str_shows_ok_for_valid(env):
    report = check_expiry(env, ["TOKEN_EXPIRY"], reference_date=REF)
    assert "ok" in str(report.entries[0])


def test_slash_date_format_parsed():
    env = {"EXP": "2023/01/01"}
    report = check_expiry(env, ["EXP"], reference_date=REF)
    assert len(report.entries) == 1
    assert report.entries[0].is_expired
