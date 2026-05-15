"""Tests for envguard.digester."""
from __future__ import annotations

import pytest

from envguard.digester import DigestResult, digest_env


SAMPLE: dict[str, str] = {
    "APP_ENV": "production",
    "DB_HOST": "localhost",
    "SECRET_KEY": "s3cr3t",
}


# ---------------------------------------------------------------------------
# digest_env
# ---------------------------------------------------------------------------

def test_returns_digest_result():
    result = digest_env(SAMPLE)
    assert isinstance(result, DigestResult)


def test_sha256_digest_is_64_hex_chars():
    result = digest_env(SAMPLE, algorithm="sha256")
    assert len(result.digest) == 64
    assert all(c in "0123456789abcdef" for c in result.digest)


def test_md5_digest_is_32_hex_chars():
    result = digest_env(SAMPLE, algorithm="md5")
    assert len(result.digest) == 32


def test_key_count_matches_input():
    result = digest_env(SAMPLE)
    assert result.key_count == len(SAMPLE)


def test_digest_is_stable_across_calls():
    r1 = digest_env(SAMPLE)
    r2 = digest_env(SAMPLE)
    assert r1.digest == r2.digest


def test_insertion_order_does_not_affect_digest():
    env_a = {"A": "1", "B": "2"}
    env_b = {"B": "2", "A": "1"}
    assert digest_env(env_a).digest == digest_env(env_b).digest


def test_different_values_produce_different_digest():
    other = {**SAMPLE, "APP_ENV": "staging"}
    assert digest_env(SAMPLE).digest != digest_env(other).digest


def test_no_previous_means_not_changed():
    result = digest_env(SAMPLE)
    assert result.previous is None
    assert result.changed is False


def test_same_previous_is_unchanged():
    base = digest_env(SAMPLE)
    result = digest_env(SAMPLE, previous=base.digest)
    assert result.changed is False


def test_different_previous_is_changed():
    result = digest_env(SAMPLE, previous="deadbeef" * 8)
    assert result.changed is True


def test_unsupported_algorithm_raises():
    with pytest.raises(ValueError, match="Unsupported algorithm"):
        digest_env(SAMPLE, algorithm="sha512")


def test_str_contains_digest():
    result = digest_env(SAMPLE)
    assert result.digest in str(result)


def test_str_contains_changed_status_when_previous_given():
    result = digest_env(SAMPLE, previous="deadbeef" * 8)
    assert "CHANGED" in str(result)


def test_str_contains_unchanged_status_when_same():
    base = digest_env(SAMPLE)
    result = digest_env(SAMPLE, previous=base.digest)
    assert "UNCHANGED" in str(result)
