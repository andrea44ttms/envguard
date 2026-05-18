"""Standalone demo for the archiver CLI (no real files needed)."""
from __future__ import annotations

import argparse
import tempfile
import os

from envguard.archiver import archive_env, load_archive_index


SAMPLE_ENV = {
    "APP_NAME": "demo-app",
    "DB_HOST": "localhost",
    "DB_PASSWORD": "hunter2",
    "SECRET_KEY": "abc123",
    "PORT": "5432",
}


def _args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="envguard archiver demo")
    p.add_argument("--no-redact", action="store_true", default=False)
    return p.parse_args([])


def run_demo() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        arch_dir = os.path.join(tmpdir, "archive")

        print("=== Archiving env (redacted) ===")
        r1 = archive_env(SAMPLE_ENV, directory=arch_dir, redact=True)
        print(r1)

        print("\n=== Archiving env again ===")
        r2 = archive_env(SAMPLE_ENV, directory=arch_dir, redact=True)
        print(r2)

        print("\n=== Archive index ===")
        index = load_archive_index(arch_dir)
        print(index)
        print(f"Latest: {index.latest()}")


if __name__ == "__main__":  # pragma: no cover
    run_demo()
