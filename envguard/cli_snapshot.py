"""CLI helpers for snapshot commands: capture, compare, and display snapshots."""

from __future__ import annotations

import sys
from typing import Dict, List, Optional

from envguard.snapshot import (
    EnvSnapshot,
    diff_snapshots,
    load_snapshot,
    save_snapshot,
    take_snapshot,
)


def cmd_capture(
    env: Dict[str, str],
    output_path: str,
    errors: Optional[List[str]] = None,
    redact_keys: Optional[List[str]] = None,
) -> EnvSnapshot:
    """Capture the current env state and persist it to *output_path*."""
    snap = take_snapshot(env, errors=errors, redact_keys=redact_keys)
    save_snapshot(snap, output_path)
    print(f"Snapshot saved → {output_path}")
    print(f"  {snap}")
    return snap


def cmd_show(snapshot_path: str) -> None:
    """Print a human-readable summary of a saved snapshot."""
    try:
        snap = load_snapshot(snapshot_path)
    except FileNotFoundError:
        print(f"ERROR: snapshot file not found: {snapshot_path}", file=sys.stderr)
        sys.exit(1)

    print(str(snap))
    print(f"  Variables ({len(snap.values)}):")
    for key, val in sorted(snap.values.items()):
        print(f"    {key}={val}")
    if snap.errors:
        print(f"  Errors ({len(snap.errors)}):")
        for err in snap.errors:
            print(f"    - {err}")


def cmd_diff(old_path: str, new_path: str) -> int:
    """Compare two snapshots and print a diff. Returns exit code (0 = no changes)."""
    try:
        old = load_snapshot(old_path)
        new = load_snapshot(new_path)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    changes = diff_snapshots(old, new)

    if not changes:
        print("No changes detected between snapshots.")
        return 0

    print(f"{len(changes)} change(s) detected:")
    for key, delta in changes.items():
        old_val = delta["old"] if delta["old"] is not None else "<absent>"
        new_val = delta["new"] if delta["new"] is not None else "<absent>"
        print(f"  {key}: {old_val!r} → {new_val!r}")
    return 1
