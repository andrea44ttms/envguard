"""CLI entry-point for the env digester."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envguard.digester import digest_env
from envguard.loader import EnvFileNotFoundError, EnvParseError, load_env_file


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envguard-digest",
        description="Compute or compare a deterministic digest of a .env file.",
    )
    p.add_argument("env_file", help="Path to the .env file")
    p.add_argument(
        "--algorithm",
        choices=("sha256", "md5"),
        default="sha256",
        help="Hash algorithm (default: sha256)",
    )
    p.add_argument(
        "--previous",
        metavar="DIGEST",
        default=None,
        help="Previous digest to compare against",
    )
    p.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Output result as JSON",
    )
    return p


def cmd_digest(args: argparse.Namespace) -> int:
    path = Path(args.env_file)
    try:
        env = load_env_file(path)
    except EnvFileNotFoundError:
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2
    except EnvParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result = digest_env(env, algorithm=args.algorithm, previous=args.previous)

    if args.as_json:
        import json
        payload = {
            "digest": result.digest,
            "algorithm": result.algorithm,
            "key_count": result.key_count,
        }
        if result.previous is not None:
            payload["previous"] = result.previous
            payload["changed"] = result.changed
        print(json.dumps(payload, indent=2))
    else:
        print(result)

    return 1 if result.changed else 0


def main() -> None:  # pragma: no cover
    sys.exit(cmd_digest(_build_arg_parser().parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()
