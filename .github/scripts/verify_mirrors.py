#!/usr/bin/env python3
"""Verify that shared hook scripts and examples stay byte-identical across cn/ and en/."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHARED_FILES = [
    "guardrails/hooks/block-dangerous.py",
    "guardrails/hooks/block-dangerous.ps1",
    "guardrails/hooks/block-dangerous.sh",
    "guardrails/hooks/tests/run_hook_tests.py",
    "guardrails/hooks/examples/claude-settings.windows.json",
    "guardrails/hooks/examples/claude-settings.windows-powershell.json",
    "guardrails/hooks/examples/claude-settings.unix.json",
]


def main() -> int:
    errors = 0
    for rel in SHARED_FILES:
        cn_path = ROOT / "cn" / rel
        en_path = ROOT / "en" / rel
        if not cn_path.exists() or not en_path.exists():
            print(f"MISSING: {rel} (cn={cn_path.exists()}, en={en_path.exists()})")
            errors += 1
            continue
        if cn_path.read_bytes() != en_path.read_bytes():
            print(f"DRIFT DETECTED: {rel}")
            errors += 1
    if errors:
        return 1
    print(f"MIRROR_SYNC_OK: {len(SHARED_FILES)} shared hook files byte-identical")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
