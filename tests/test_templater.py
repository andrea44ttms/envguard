"""Tests for envguard.templater."""
from __future__ import annotations

import pytest

from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType
from envguard.templater import TemplateOptions, TemplateResult, generate_template


@pytest.fixture()
def schema() -> EnvSchema:
    s = EnvSchema()
    s.add("APP_ENV", EnvVarSchema(type=EnvVarType.STRING, required=True, description="Deployment environment"))
    s.add("PORT", EnvVarSchema(type=EnvVarType.INTEGER, required=False, default=8000))
    s.add("DEBUG", EnvVarSchema(type=EnvVarType.BOOLEAN, required=False, default=False))
    s.add("SECRET", EnvVarSchema(type=EnvVarType.STRING, required=True))
    return s


def test_returns_template_result(schema):
    result = generate_template(schema)
    assert isinstance(result, TemplateResult)


def test_var_counts(schema):
    result = generate_template(schema)
    assert result.var_count == 4
    assert result.required_count == 2
    assert result.optional_count == 2


def test_required_var_uses_placeholder(schema):
    result = generate_template(schema)
    assert "APP_ENV=<APP_ENV>" in result.content


def test_optional_var_uses_default(schema):
    result = generate_template(schema)
    assert "PORT=8000" in result.content


def test_optional_bool_default(schema):
    result = generate_template(schema)
    assert "DEBUG=False" in result.content


def test_no_defaults_leaves_optional_empty(schema):
    options = TemplateOptions(include_defaults=False)
    result = generate_template(schema, options)
    assert "PORT=\n" in result.content or result.content.count("PORT=") == 1


def test_comments_included_by_default(schema):
    result = generate_template(schema)
    assert "[required]" in result.content
    assert "[optional]" in result.content


def test_description_in_comment(schema):
    result = generate_template(schema)
    assert "Deployment environment" in result.content


def test_type_annotation_in_comment_for_non_string(schema):
    result = generate_template(schema)
    assert "type=integer" in result.content


def test_no_comments_option(schema):
    options = TemplateOptions(include_comments=False)
    result = generate_template(schema, options)
    assert "#" not in result.content


def test_custom_placeholder_style(schema):
    options = TemplateOptions(placeholder_style="{{{{ {name} }}}}")
    result = generate_template(schema, options)
    assert "APP_ENV={{ APP_ENV }}" in result.content


def test_content_ends_with_newline(schema):
    result = generate_template(schema)
    assert result.content.endswith("\n")


def test_all_keys_present(schema):
    result = generate_template(schema)
    for key in ("APP_ENV", "PORT", "DEBUG", "SECRET"):
        assert key in result.content
