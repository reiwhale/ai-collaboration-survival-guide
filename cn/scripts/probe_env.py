#!/usr/bin/env python3
"""
跨平台只读宿主机环境自画像脚本（Probe Host Environment）
用途：一次性收集 OS、Shell、编码、常用开发工具链及已知平台陷阱，生成本地忽略文件 `.agent-env.local.txt`。
安全约束：仅使用只读探测；绝不读取环境变量明文、`.env`、密钥、Token 或个人隐私目录。
"""

from __future__ import annotations

import argparse
import datetime
import locale
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

TOOL_SPECS: list[tuple[str, list[str], list[str]]] = [
    ("git", ["git"], ["--version"]),
    ("python", ["python3", "python", "py"], ["--version"]),
    ("node", ["node"], ["-v"]),
    ("npm", ["npm.cmd", "npm"] if os.name == "nt" else ["npm"], ["-v"]),
    ("pnpm", ["pnpm.cmd", "pnpm"] if os.name == "nt" else ["pnpm"], ["-v"]),
    ("uv", ["uv"], ["--version"]),
    ("go", ["go"], ["version"]),
    ("cargo", ["cargo"], ["--version"]),
    ("rustc", ["rustc"], ["--version"]),
    ("java", ["java"], ["-version"]),
    ("gcc", ["gcc"], ["--version"]),
    ("rg", ["rg"], ["--version"]),
    ("docker", ["docker"], ["--version"]),
]


def _run_readonly(cmd: list[str], timeout: float = 2.5) -> str:
    """Run a quick read-only version command and return its first non-empty output line."""
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        raw = (proc.stdout or "") + "\n" + (proc.stderr or "")
        for line in raw.splitlines():
            stripped = line.strip()
            if stripped:
                return stripped[:120]
        return f"(exit={proc.returncode}, no output)"
    except Exception as exc:
        return f"(probe failed: {type(exc).__name__})"


def _detect_os_info() -> str:
    """Detect human-accurate OS version (handling Windows 11 Build >= 22000 correctly)."""
    machine = platform.machine()
    if os.name == "nt" and hasattr(sys, "getwindowsversion"):
        win = sys.getwindowsversion()
        if win.major == 10 and win.build >= 22000:
            return f"Windows 11 (Build {win.build}, {machine})"
        return f"Windows {platform.release()} (Build {win.build}, {machine})"
    return f"{platform.system()} {platform.release()} ({machine})"


def _detect_shell_notes() -> list[str]:
    """Inspect shell availability and common platform pitfalls without touching secrets."""
    notes: list[str] = []
    if os.name == "nt":
        ps5 = shutil.which("powershell")
        pwsh7 = shutil.which("pwsh")
        notes.append(f"powershell_5_1: {'available' if ps5 else 'missing'}")
        notes.append(f"pwsh_7: {'available' if pwsh7 else 'missing (do NOT call pwsh)'}")
        if ps5:
            policy = _run_readonly(["powershell", "-NoProfile", "-Command", "Get-ExecutionPolicy"])
            notes.append(f"powershell_execution_policy: {policy}")
            if "Restricted" in policy or "AllSigned" in policy:
                notes.append("pitfall_ps_wrapper: npm/pnpm .ps1 wrappers may be blocked -> use npm.cmd / pnpm.cmd")
        notes.append("pitfall_ps5_encoding: PowerShell 5.1 misreads UTF-8 without BOM -> prefer .py / .mjs for text processing")
        notes.append("pitfall_ps5_syntax: PowerShell 5.1 does not support '&&' chaining -> use separate lines or ';'")
    else:
        shell_bin = Path(os.environ.get("SHELL", "/bin/sh")).name
        notes.append(f"default_shell_name: {shell_bin}")
        notes.append("line_ending: LF")
    return notes


def _detect_tools() -> tuple[list[str], list[str]]:
    """Probe installed CLI toolchains and record available versions vs missing binaries."""
    found: list[str] = []
    missing: list[str] = []
    for label, candidates, args in TOOL_SPECS:
        exe_path = None
        used_cmd = ""
        for cand in candidates:
            resolved = shutil.which(cand)
            if resolved:
                exe_path = resolved
                used_cmd = cand
                break
        if exe_path:
            ver = _run_readonly([exe_path, *args])
            found.append(f"- {label} (`{used_cmd}`): {ver}")
        else:
            missing.append(label)
    return found, missing


def build_profile(workspace_dir: Path) -> str:
    """Build concise host environment profile text for local agent consumption."""
    now_str = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %z")
    sys_info = _detect_os_info()
    py_ver = platform.python_version()
    pref_enc = locale.getpreferredencoding(False)
    has_git_repo = (workspace_dir / ".git").exists()

    shell_notes = _detect_shell_notes()
    found_tools, missing_tools = _detect_tools()

    lines = [
        "# .agent-env.local.txt (LOCAL ONLY - DO NOT COMMIT TO GIT)",
        "# 更新暗号: 对 AI 发送 `同步本地环境` 或 `/sync-env` 即可重跑本档案。",
        f"generated_at: {now_str}",
        f"os: {sys_info}",
        f"python_runtime: {py_ver}",
        f"locale_preferred_encoding: {pref_enc}",
        f"workspace_git_initialized: {'YES' if has_git_repo else 'NO (WARNING: run git init before letting AI edit files!)'}",
        "",
        "[shell_and_platform_notes]",
        *[f"- {item}" for item in shell_notes],
        "",
        "[available_toolchains]",
        *(found_tools if found_tools else ["- (none detected)"]),
        "",
        "[not_in_path_do_not_call]",
        f"- {', '.join(missing_tools) if missing_tools else '(none)'}",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Generate local-only host environment profile for AI coding agents.")
    parser.add_argument(
        "--output",
        default=".agent-env.local.txt",
        help="Output file path (default: .agent-env.local.txt in current working directory)",
    )
    parser.add_argument(
        "--workspace",
        default=None,
        help="Target workspace directory to check for .git (default: current working directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print profile to stdout without writing file",
    )
    args = parser.parse_args()

    out_path = Path(args.output).resolve()
    ws_dir = Path(args.workspace).resolve() if args.workspace else Path.cwd().resolve()
    content = build_profile(ws_dir)

    if args.dry_run:
        print(content)
        return 0

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8", newline="\n")
    size_bytes = out_path.stat().st_size
    print(f"OK: wrote {out_path.name} ({size_bytes} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
