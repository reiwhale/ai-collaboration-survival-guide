# PreToolUse Speed-Bump Hook Setup Guide

> Text-only warnings in `AGENTS.md` fade under context compaction.  
> A **`PreToolUse` hook** inspects each shell command right before execution via a zero-dependency lexer engine and exits with **`exit 2`** (Claude Code's deterministic block code) on high-risk slips.
>
> ⚠️ **Honest Scope (Speed Bump, Not a Sandbox)**: Even with the cross-platform lexer engine [`block-dangerous.py`](block-dangerous.py) (handling nested quotes, comments, heredocs, multi-line commits, pipelines, and common variants), hooks cannot catch every equivalent bypass (see Section 4). **Your real safety net is always Git local checkpoints + your IDE/CLI's native approval prompt.**

---

## 1. Installing in Claude Code (`.claude/settings.json`)

> **Host Compatibility**: The JSON snippets below are formatted for **Claude Code**. If you use **Cursor, Codex CLI, Gemini CLI, or Antigravity**, use [`AGENTS.lite.md`](../../templates/AGENTS.lite.md) + **Git checkpoints** + your tool's built-in command confirmation dialog.

### Step 1: Copy Hook Files into `.claude/hooks/`
- **Recommended (Fastest & Cross-Shell Safe)**: Copy [`block-dangerous.py`](block-dangerous.py) into `.claude/hooks/`. If you prefer the `.sh` or `.ps1` wrapper, copy both `block-dangerous.py` and the wrapper into `.claude/hooks/` (the wrapper automatically delegates to `block-dangerous.py` when Python is available and falls back to portable POSIX `awk` / PowerShell when Python is absent).

### Step 2: Add One Snippet to `.claude/settings.json` (Ready-Made Files in [`examples/`](examples/))

#### Option A · Cross-Platform Python Engine (Recommended — Works in All Windows Shells, macOS & Linux)
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python -B .claude/hooks/block-dangerous.py"
          }
        ]
      }
    ]
  }
}
```
> Ready-made file: [`examples/claude-settings.windows.json`](examples/claude-settings.windows.json). Forward-slash relative paths work cleanly across **cmd.exe, PowerShell 5.1, and Git Bash** on Windows without triggering `%CLAUDE_PROJECT_DIR%` expansion failures in Git Bash. (On macOS/Linux systems where only `python3` exists, swap `python` to `python3` or use Option B.)

#### Option B · macOS / Linux / Git Bash Wrapper (Auto-Fallback if Python Is Missing)
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/block-dangerous.sh\""
          }
        ]
      }
    ]
  }
}
```
> Ready-made file: [`examples/claude-settings.unix.json`](examples/claude-settings.unix.json). Make executable once: `chmod +x .claude/hooks/block-dangerous.sh`.

#### Option C · Windows PowerShell Wrapper (`Restricted` Execution Policy Safe)
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "powershell -NoProfile -ExecutionPolicy Bypass -File .claude/hooks/block-dangerous.ps1"
          }
        ]
      }
    ]
  }
}
```
> Ready-made file: [`examples/claude-settings.windows-powershell.json`](examples/claude-settings.windows-powershell.json). If your setup invokes hooks from a subdirectory rather than the project root, replace the relative path with an explicit absolute path using forward slashes `/`.

---

## 2. Two-Step Mandatory Verification (Guard Against Silent Fail-Open)

> ⚠️ **Fail-Open Risk**: In Claude Code's hook contract, only **`exit 2`** blocks execution. If the script path is wrong, lacks execute permission, or crashes with any other non-zero exit code (`exit 1` / `127`), **the host fails open and lets the command run**. Always verify both steps:

### Step 1: Local Script Self-Test
- **Cross-platform Python engine**:
  ```bash
  python -B .claude/hooks/block-dangerous.py --test "rm -rf *.py"
  ```
- **macOS / Linux / Git Bash**:
  ```bash
  bash .claude/hooks/block-dangerous.sh --test "rm -rf *.py" ; echo "EXIT=$?"
  # Expected: BLOCKED BY GUARDRAIL ... and EXIT=2
  ```
- **Windows PowerShell**:
  ```powershell
  powershell -NoProfile -ExecutionPolicy Bypass -File .claude/hooks/block-dangerous.ps1 -TestCommand "rm -rf *.py"
  echo "EXIT=$LASTEXITCODE"   # Expected: BLOCKED BY GUARDRAIL ... and EXIT=2
  ```
- Run the full reproducible test suite (red-team bypasses, false-positive guards, 64 KB payload deadlock guard, malformed JSON, and no-Python shell fallback) from the repo root:
  ```bash
  python en/guardrails/hooks/tests/run_hook_tests.py
  python cn/guardrails/hooks/tests/run_hook_tests.py
  ```

### Step 2: Live Wiring Check Inside Claude Code (Critical!)
Reload Claude Code and ask it to run a harmless probe via its Bash tool:
```text
Please run via Bash: rm -rf *.probe_nonexistent_999
```
- ✅ **Tool call blocked with `BLOCKED BY GUARDRAIL`** -> Wiring is live.
- ❌ **Command runs silently** -> Check `.claude/settings.json` path or permissions; your hook is failing open!

---

## 3. Tested Platform Matrix & Cross-Platform Notes

| Platform | Entry Script | Engine & Fallback | Notes |
|---|---|---|---|
| **Windows 11 (PowerShell 5.1 / cmd / Git Bash)** | [`block-dangerous.py`](block-dangerous.py) / [`block-dangerous.ps1`](block-dangerous.ps1) / [`block-dangerous.sh`](block-dangerous.sh) | Zero-dependency `.py` lexer; falls back to PS1 / POSIX `awk` when Python is absent | `.ps1` requires `-NoProfile -ExecutionPolicy Bypass`; Option A (`.py`) avoids Windows shell quoting differences |
| **macOS / Linux** | [`block-dangerous.py`](block-dangerous.py) / [`block-dangerous.sh`](block-dangerous.sh) | Uses `python3` + `.py`; falls back to portable POSIX `awk` (BSD & GNU safe, no GNU `sed` `\n`) | Not run on authors' local Mac/Linux hardware; verified via GitHub Actions `macos-latest` & `ubuntu-latest` CI — still complete both local checks above |

---

## 4. Scope & Documented Bypass Boundaries

- **What this speed bump blocks**:
  - Wildcard deletes (including PowerShell quoted wildcards & pipelines): `rm *.py`, `rm -rf "*.py"`, `Remove-Item "*.py"`, `Get-ChildItem *.py | % { Remove-Item $_ }`, `find ... -delete / -execdir rm`, `xargs /bin/rm`, `cmd /c del /f /s /q *.py`;
  - Recursive root / drive / home / cwd / parent wipes: `rm -rf /`, `~/`, `$HOME`, `.`, `./`, `../`, `Remove-Item -Rec -Fo .`, `ri -r -fo .`, `$env:USERPROFILE`, `rd /s /q C:\`;
  - Destructive Git (including global flags like `-C`, `--no-pager`, and reordered flags): `git reset --hard`, `git clean -f` (allows `-n/--dry-run`), `git push -f / --force / -fu / --mirror` (allows `--force-with-lease`), `git checkout/restore .` & `./`, `git stash clear/drop`, `git branch -D`;
  - Destructive DB / IaC / disk commands: `DROP TABLE/DATABASE/SCHEMA`, `TRUNCATE [TABLE]`, `terraform destroy` / `apply -destroy`, `mkfs.*`, `dd of=/dev/...`, `chmod -R /`;
  - Wrapper & lexer hardening: inspects `bash -c`, `powershell -c`, `cmd /c`, `eval`, `$(...)`, `(rm -rf /)`, `sudo -u root`, and `r\m`, while preventing quote-desync bypasses and 64 KB pipe deadlocks.
  - **Low false positives**: Native lexer tracks multi-line quotes, heredocs, trailing `#` comments, and per-segment command names so `cd app && git commit -m "fix DROP TABLE"`, `cat << 'EOF' ...`, `python -c "assert 'DROP TABLE'..."`, `pytest -k "DROP TABLE"`, `ls | xargs grep -n rm`, `rm old.log # delete?`, and `Remove-Item -Recurse -Force .\node_modules` all pass cleanly.
- **What it intentionally does NOT catch (known bypasses)**:
  - **Named directory wipes**: `rm -rf src`, `Remove-Item -Recurse -Force src`, `cmd /c rd /s /q src` (cannot reliably distinguish `node_modules` from business folders);
  - **Inline script deletions**: `python -c "import os..."`, `node -e "fs.rmSync(...)"`;
  - **Git refspec force syntax**: `git push origin +main`;
  - **Non-shell IDE APIs**: Native file-delete tools bypass Bash hooks entirely.
- **Bottom line**: Treat hooks as a **first-line speed bump**, never a reason to skip Git checkpoints or disable host approval prompts.
