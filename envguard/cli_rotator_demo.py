"""Quick demo / smoke-test for the rotator CLI (not part of the test suite)."""
from __future__ import annotations

import tempfile
import os

from envguard.cli_rotator import cmd_rotate


SAMPLE_ENV = """
APP_NAME=myapp
PORT=8080
DB_PASSWORD=supersecret
API_KEY=CHANGEME
SECRET_TOKEN=
DEBUG=false
""".strip()


def _args(path, fmt="text"):
    class A:
        env_file = path
        placeholder = "CHANGEME"
        no_empty_check = False
        format = fmt
        reason = None

    return A()


def run_demo() -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".env", delete=False
    ) as fh:
        fh.write(SAMPLE_ENV)
        tmp = fh.name

    try:
        print("=== TEXT output ===")
        exit_code = cmd_rotate(_args(tmp, fmt="text"))
        print(f"\nExit code: {exit_code}")

        print("\n=== JSON output ===")
        cmd_rotate(_args(tmp, fmt="json"))
    finally:
        os.unlink(tmp)


if __name__ == "__main__":  # pragma: no cover
    run_demo()
