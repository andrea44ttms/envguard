"""CLI command for tracing env var origins across multiple .env files."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envguard.loader import load_env_file, EnvFileNotFoundError, EnvParseError
from envguard.tracer import trace_env


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envguard-trace",
        description="Trace env var origins across multiple .env files (lowest to highest priority).",
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help=".env files ordered from lowest to highest priority",
    )
    parser.add_argument(
        "--key",
        metavar="KEY",
        default=None,
        help="Show trace for a single key only",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    return parser


def cmd_trace(args: argparse.Namespace) -> int:
    sources = []
    for filepath in args.files:
        path = Path(filepath)
        try:
            env = load_env_file(path)
        except EnvFileNotFoundError:
            print(f"error: file not found: {filepath}", file=sys.stderr)
            return 2
        except EnvParseError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        sources.append((path.name, env))

    result = trace_env(sources)

    if args.key:
        trace = result.get(args.key)
        if trace is None:
            print(f"Key '{args.key}' not found in any source.", file=sys.stderr)
            return 1
        keys_to_show = [args.key]
    else:
        keys_to_show = result.all_keys

    if args.format == "json":
        output = {}
        for key in keys_to_show:
            t = result.traces[key]
            output[key] = {
                "active_value": t.active_value,
                "active_source": t.active_source,
                "history": [
                    {"source": e.source, "value": e.value, "overridden_by": e.overridden_by}
                    for e in t.entries
                ],
            }
        print(json.dumps(output, indent=2))
    else:
        for key in keys_to_show:
            print(result.traces[key])

    return 0


def main() -> None:  # pragma: no cover
    parser = _build_arg_parser()
    args = parser.parse_args()
    sys.exit(cmd_trace(args))


if __name__ == "__main__":  # pragma: no cover
    main()
