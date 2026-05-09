"""Generate .env template files from an EnvSchema definition."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from envguard.schema import EnvSchema, EnvVarType


@dataclass
class TemplateOptions:
    include_comments: bool = True
    include_defaults: bool = True
    placeholder_style: str = "<{name}>"  # supports {name} and {type}
    section_separator: bool = True


@dataclass
class TemplateResult:
    content: str
    var_count: int
    required_count: int
    optional_count: int

    def __str__(self) -> str:  # pragma: no cover
        return self.content


def _placeholder(name: str, var_type: EnvVarType, style: str) -> str:
    type_name = var_type.value
    return style.format(name=name, type=type_name)


def generate_template(
    schema: EnvSchema,
    options: Optional[TemplateOptions] = None,
) -> TemplateResult:
    """Render a .env template from the given schema."""
    if options is None:
        options = TemplateOptions()

    lines: list[str] = []
    required_count = 0
    optional_count = 0

    if options.include_comments:
        lines.append("# Auto-generated .env template")
        lines.append("# Fill in the values below before starting the application.")
        if options.section_separator:
            lines.append("")

    for name, var in schema.vars.items():
        if options.include_comments:
            tag = "[required]" if var.required else "[optional]"
            desc = var.description or ""
            comment_parts = [tag]
            if desc:
                comment_parts.append(desc)
            if var.type != EnvVarType.STRING:
                comment_parts.append(f"type={var.type.value}")
            lines.append(f"# {' | '.join(comment_parts)}")

        if var.required:
            value = _placeholder(name, var.type, options.placeholder_style)
            required_count += 1
        else:
            if options.include_defaults and var.default is not None:
                value = str(var.default)
            else:
                value = ""
            optional_count += 1

        lines.append(f"{name}={value}")

        if options.include_comments and options.section_separator:
            lines.append("")

    content = "\n".join(lines).rstrip() + "\n"
    return TemplateResult(
        content=content,
        var_count=len(schema.vars),
        required_count=required_count,
        optional_count=optional_count,
    )
