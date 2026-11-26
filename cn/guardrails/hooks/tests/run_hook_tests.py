#!/usr/bin/env python3
"""
Reproducible test suite for guardrails/hooks/block-dangerous.{py,ps1,sh}.
Run from repo root:
    python en/guardrails/hooks/tests/run_hook_tests.py
    python cn/guardrails/hooks/tests/run_hook_tests.py
"""
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HOOKS_DIR = Path(__file__).resolve().parent.parent
PY_PATH = HOOKS_DIR / "block-dangerous.py"
PS1_PATH = HOOKS_DIR / "block-dangerous.ps1"
SH_PATH = HOOKS_DIR / "block-dangerous.sh"

# (category, command, expect_ps, expect_sh)
# B = must block (exit 2), P = must pass (exit 0)
CASES = [
    # --- Core claimed blocks ---
    ("claim", "rm *.py", "B", "B"),
    ("claim", "rm -rf *.py", "B", "B"),
    ("claim", "rm -rf ./*.py", "B", "B"),
    ("claim", 'rm -rf "*.py"', "B", "B"),
    ("claim", "Remove-Item *.py", "B", "P"),
    ("claim", 'Remove-Item "*.py"', "B", "P"),
    ("claim", "Remove-Item '*.py'", "B", "P"),
    ("claim", 'del "*.py"', "B", "P"),
    ("claim", "Get-ChildItem *.py | Remove-Item", "B", "P"),
    ("claim", "Get-ChildItem *.py | % { Remove-Item $_ }", "B", "P"),
    ("claim", "Get-ChildItem *.py | ForEach-Object { rm $_ }", "B", "P"),
    ("claim", "Remove-Item -Recurse -Force C:\\", "B", "P"),
    ("claim", "Remove-Item -Recurse -Force .", "B", "P"),
    ("claim", 'Remove-Item -Recurse -Force "."', "B", "P"),
    ("claim", "Remove-Item -Recurse -Force ./", "B", "P"),
    ("claim", "Remove-Item -Recurse -Force ../", "B", "P"),
    ("claim", "Remove-Item -Rec -Fo .", "B", "P"),
    ("claim", "Remove-Item -Rec -Fo C:\\", "B", "P"),
    ("claim", "ri -r -fo .", "B", "P"),
    ("claim", "Remove-Item . -Recurse -Force", "B", "P"),
    ("claim", "Remove-Item -LiteralPath C:\\ -Recurse -Force", "B", "P"),
    ("claim", "Remove-Item -Recurse -Force $env:USERPROFILE", "B", "P"),
    ("claim", "rd /s /q C:\\", "B", "P"),
    ("claim", "cmd /c del /f /s /q *.py", "B", "B"),
    ("claim", "cmd /c rd /s /q C:\\", "B", "B"),
    ("claim", "rm -rf ./", "B", "B"),
    ("claim", "rm -rf ../", "B", "B"),
    ("claim", 'rm -rf "/"', "B", "B"),
    ("claim", 'rm -rf "."', "B", "B"),
    ("claim", 'rm -rf "~"', "B", "B"),
    ("claim", "rm -rf ~/", "B", "B"),
    ("claim", "rm -rf $HOME/", "B", "B"),
    ("claim", "rm -rf ${HOME}", "B", "B"),
    ("claim", "rm -rf -- /", "B", "B"),
    ("claim", "rm / -rf", "B", "B"),
    ("claim", "rm --recursive --force /", "B", "B"),
    ("claim", "rm.exe -rf *.py", "B", "B"),
    ("claim", "find . -name '*.py' -delete", "B", "B"),
    ("claim", "find . -name '*.py' -execdir rm {} +", "B", "B"),
    ("claim", "find . -name '*.py' -exec /bin/rm {} +", "B", "B"),
    ("claim", "ls *.tmp | xargs rm", "B", "B"),
    ("claim", "ls *.tmp | xargs /bin/rm", "B", "B"),
    ("claim", "rm -rf /", "B", "B"),
    ("claim", "rm -rf ~", "B", "B"),
    ("claim", "rm -rf .", "B", "B"),
    # --- Red-team bypass hardening ---
    ("redteam", "echo '\"' ; rm -rf / # \"", "B", "B"),
    ("redteam", "echo '\"' && git reset --hard HEAD~1 # \"", "B", "B"),
    ("redteam", "sudo -u root rm -rf /", "B", "B"),
    ("redteam", "env -i rm -rf /", "B", "B"),
    ("redteam", "command -p rm -rf /", "B", "B"),
    ("redteam", "timeout 10 rm -rf /", "B", "B"),
    ("redteam", r"r\m -rf *.py", "B", "B"),
    ("redteam", "/bin/rm -rf /", "B", "B"),
    ("redteam", "& Remove-Item *.py", "B", "P"),
    ("redteam", "(rm -rf /)", "B", "B"),
    ("redteam", "$(rm -rf *.py)", "B", "B"),
    ("redteam", "{ rm -rf /; }", "B", "B"),
    ("redteam", "if true; then rm -rf /; fi", "B", "B"),
    ("redteam", 'bash -c "rm -rf *.py"', "B", "B"),
    ("redteam", 'powershell -c "Remove-Item *.py"', "B", "B"),
    ("redteam", 'eval "rm -rf /"', "B", "B"),
    # --- Destructive Git & variants ---
    ("claim", "git reset --hard HEAD~1", "B", "B"),
    ("claim", "git -C . reset --hard HEAD~1", "B", "B"),
    ("claim", "git reset HEAD~1 --hard", "B", "B"),
    ("claim", "git clean -fd", "B", "B"),
    ("claim", "git --no-pager clean -fdx", "B", "B"),
    ("claim", "git clean --force -d", "B", "B"),
    ("claim", "git clean -d -f", "B", "B"),
    ("claim", "git push -f origin main", "B", "B"),
    ("claim", "git push --force origin main", "B", "B"),
    ("claim", "git -C . push --force origin main", "B", "B"),
    ("claim", "git push -fu origin main", "B", "B"),
    ("claim", "git push --force=true origin main", "B", "B"),
    ("claim", "git push --mirror origin", "B", "B"),
    ("claim", "git stash drop", "B", "B"),
    ("claim", "git stash clear", "B", "B"),
    ("claim", "git restore .", "B", "B"),
    ("claim", "git restore ./", "B", "B"),
    ("claim", "git restore --worktree .", "B", "B"),
    ("claim", "git checkout -- .", "B", "B"),
    ("claim", "git checkout HEAD -- .", "B", "B"),
    ("claim", "git branch -D main", "B", "B"),
    # --- Destructive DB / IaC / Disk ---
    ("claim", "DROP TABLE users;", "B", "B"),
    ("claim", 'psql -c "DROP TABLE users;"', "B", "B"),
    ("claim", 'echo ok && psql -c "DROP TABLE users;"', "B", "B"),
    ("claim", 'git status; psql -c "TRUNCATE TABLE logs;"', "B", "B"),
    ("claim", 'psql -c "TRUNCATE users;"', "B", "B"),
    ("claim", "psql -c \"DROP\nTABLE users;\"", "B", "B"),
    ("claim", "TRUNCATE TABLE logs;", "B", "B"),
    ("claim", "terraform destroy -auto-approve", "B", "B"),
    ("claim", "terraform apply -destroy -auto-approve", "B", "B"),
    ("claim", "mkfs.ext4 /dev/sda1", "B", "B"),
    ("claim", "dd if=/dev/zero of=/dev/sda", "B", "B"),
    ("claim", "chmod -R 777 /", "B", "B"),
    # --- False-positive guard (must pass) ---
    ("false+", "git commit -m 'chore: rm temp files?'", "P", "P"),
    ("false+", 'git commit -m "refactor: rm dead code\n\n* tidy utils"', "P", "P"),
    ("false+", 'git commit -m "docs: warn against dangerous commands\n\nrm -rf *.py\ngit reset --hard"', "P", "P"),
    ("false+", "cat << 'EOF' > safety.md\nNever run:\nrm -rf /\ngit reset --hard\nEOF", "P", "P"),
    ("false+", 'cd app && git commit -m "fix DROP TABLE migration"', "P", "P"),
    ("false+", 'cd docs && grep -rn "DROP TABLE" .', "P", "P"),
    ("false+", 'cd repo && echo "never run TRUNCATE TABLE"', "P", "P"),
    ("false+", 'cat schema.sql | grep "DROP TABLE"', "P", "P"),
    ("false+", "python -c \"assert 'DROP TABLE' not in sql\"", "P", "P"),
    ("false+", "node -e \"console.log('Checking TRUNCATE TABLE guard')\"", "P", "P"),
    ("false+", 'pytest -k "DROP TABLE"', "P", "P"),
    ("false+", "ls | xargs grep -n rm", "P", "P"),
    ("false+", "git diff --name-only | xargs echo rm", "P", "P"),
    ("false+", "rm old.log # delete old file?", "P", "P"),
    ("false+", 'grep -rn "rm \\*" docs/', "P", "P"),
    ("false+", "curl https://example.com/api/rm/?id=1", "P", "P"),
    ("false+", "echo Should I rm this?", "P", "P"),
    ("false+", 'git commit -m "fix DROP TABLE regression"', "P", "P"),
    ("false+", "git add *.py", "P", "P"),
    ("false+", "git clean -nd", "P", "P"),
    ("false+", "git branch -d feat/done", "P", "P"),
    ("false+", "git checkout .gitignore", "P", "P"),
    ("false+", "rm -rf node_modules", "P", "P"),
    ("false+", r"Remove-Item .\build\app.log", "P", "P"),
    ("false+", r"Remove-Item -Recurse -Force .\node_modules", "P", "P"),
    ("false+", r"Remove-Item -Recurse -Force .\build", "P", "P"),
    ("false+", r"Remove-Item -Recurse -Force .\dist", "P", "P"),
    ("false+", "rm -rf ./node_modules", "P", "P"),
    ("false+", "Remove-Item -Recurse -Force ./node_modules", "P", "P"),
    ("false+", "Remove-Item -Recurse -Force .\\node_modules\\cache", "P", "P"),
    ("false+", "git push --force-with-lease", "P", "P"),
    ("false+", 'echo "never run terraform destroy blindly"', "P", "P"),
    ("false+", "git status -s", "P", "P"),
]

# Core cases also verified under pure shell fallback (GUARDRAIL_DISABLE_PYTHON=1)
FALLBACK_CASES = [
    ("fb-block", "rm -rf *.py", "B", "B"),
    ("fb-block", 'rm -rf "/"', "B", "B"),
    ("fb-block", "ls *.tmp | xargs rm", "B", "B"),
    ("fb-block", "git -C . reset --hard HEAD~1", "B", "B"),
    ("fb-block", 'echo ok && psql -c "DROP TABLE users;"', "B", "B"),
    ("fb-pass", 'cd app && git commit -m "fix DROP TABLE migration"', "P", "P"),
    ("fb-pass", "ls | xargs grep -n rm", "P", "P"),
    ("fb-pass", "rm old.log # delete old file?", "P", "P"),
    ("fb-pass", "git push --force-with-lease", "P", "P"),
    ("fb-pass", "rm -rf ./node_modules", "P", "P"),
]

# Documented bypasses: speed bump intentionally cannot replace Git + host approvals
KNOWN_BYPASSES = [
    "rm -rf src",
    "Remove-Item -Recurse -Force src",
    "cmd /c rd /s /q src",
    "git push origin +main",
    "python -c \"import glob,os;[os.remove(f) for f in glob.glob('*.py')]\"",
    "node -e \"require('fs').rmSync('src',{recursive:true})\"",
]


def find_bash():
    env_bash = os.environ.get("HOOK_TEST_BASH")
    if env_bash and Path(env_bash).exists():
        return env_bash
    candidates = [shutil.which("bash")]
    if platform.system() == "Windows":
        local_app = os.environ.get("LOCALAPPDATA", "")
        prog_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        prog_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        candidates.extend([
            str(Path(prog_files) / "Git" / "bin" / "bash.exe"),
            str(Path(prog_x86) / "Git" / "bin" / "bash.exe"),
            str(Path(local_app) / "Programs" / "Git" / "bin" / "bash.exe"),
            str(Path(local_app) / "Programs" / "GitPortable" / "bin" / "bash.exe"),
        ])
    for cand in candidates:
        if cand and Path(cand).exists():
            if "System32" in cand:
                continue
            return cand
    return None


def _env(disable_py: bool = False):
    env = os.environ.copy()
    if disable_py:
        env["GUARDRAIL_DISABLE_PYTHON"] = "1"
    else:
        env.pop("GUARDRAIL_DISABLE_PYTHON", None)
    return env


def run_py(cmd, dialect="ps", mode="stdin"):
    if mode == "stdin":
        payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
        p = subprocess.run(
            [sys.executable, "-B", str(PY_PATH), "--dialect", dialect],
            input=payload, text=True, capture_output=True, timeout=15,
        )
    else:
        p = subprocess.run(
            [sys.executable, "-B", str(PY_PATH), "--dialect", dialect, "--test", cmd],
            text=True, capture_output=True, timeout=15,
        )
    return p.returncode


def run_ps1(cmd, mode="stdin", disable_py=False):
    if mode == "stdin":
        payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
        p = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(PS1_PATH)],
            input=payload, text=True, capture_output=True, timeout=20, env=_env(disable_py),
        )
    else:
        p = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(PS1_PATH), "-TestCommand", cmd],
            text=True, capture_output=True, timeout=20, env=_env(disable_py),
        )
    return p.returncode


def run_sh(bash_exe, cmd, mode="stdin", disable_py=False):
    if mode == "stdin":
        payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
        p = subprocess.run(
            [bash_exe, str(SH_PATH)],
            input=payload, text=True, capture_output=True, timeout=20, env=_env(disable_py),
        )
    else:
        p = subprocess.run(
            [bash_exe, str(SH_PATH), "--test", cmd],
            text=True, capture_output=True, timeout=20, env=_env(disable_py),
        )
    return p.returncode


def run_raw_stdin(runner_cmd, raw_input, disable_py=False):
    p = subprocess.run(
        runner_cmd,
        input=raw_input, text=True, capture_output=True, timeout=20, env=_env(disable_py),
    )
    return p.returncode


def code_label(rc):
    if rc == 2:
        return "B"
    if rc == 0:
        return "P"
    return f"ERR({rc})"


def main():
    parser = argparse.ArgumentParser(description="Run guardrail hook test suite.")
    parser.add_argument("--require-ps", action="store_true", help="Fail if PowerShell is unavailable.")
    parser.add_argument("--require-bash", action="store_true", help="Fail if Bash is unavailable.")
    args = parser.parse_args()

    has_ps = platform.system() == "Windows" and shutil.which("powershell") is not None
    bash_exe = find_bash()

    print(
        f"Platform: {platform.system()} | Python: {PY_PATH.name} | "
        f"PowerShell: {'YES' if has_ps else 'SKIP'} | Bash: {bash_exe or 'SKIP'}"
    )
    if args.require_ps and not has_ps:
        print("ERROR: --require-ps set but powershell not available.")
        return 1
    if args.require_bash and not bash_exe:
        print("ERROR: --require-bash set but bash not available.")
        return 1
    if not PY_PATH.exists():
        print(f"ERROR: Missing engine {PY_PATH}")
        return 1

    failures = 0
    checks = 0

    # 1. Direct Python engine across both dialects (always runs on all platforms)
    for cat, cmd, exp_ps, exp_sh in CASES:
        for dialect, exp in (("ps", exp_ps), ("sh", exp_sh)):
            modes = ["stdin"] if ("\n" in cmd or '"' in cmd) else ["stdin", "arg"]
            for m in modes:
                checks += 1
                got = code_label(run_py(cmd, dialect=dialect, mode=m))
                if got != exp:
                    failures += 1
                    print(f"FAIL [py/{dialect}/{m}] [{cat}] got={got} exp={exp} cmd={cmd!r}")

    # 2. Shell wrappers (stdin mode; plus arg mode on clean single-line commands)
    for cat, cmd, exp_ps, exp_sh in CASES:
        if has_ps:
            checks += 1
            got = code_label(run_ps1(cmd, "stdin"))
            if got != exp_ps:
                failures += 1
                print(f"FAIL [ps1/stdin] [{cat}] got={got} exp={exp_ps} cmd={cmd!r}")
        if bash_exe:
            checks += 1
            got = code_label(run_sh(bash_exe, cmd, "stdin"))
            if got != exp_sh:
                failures += 1
                print(f"FAIL [sh/stdin]  [{cat}] got={got} exp={exp_sh} cmd={cmd!r}")

    # 3. Protocol robustness: 64KB payload (no deadlock), raw non-JSON, truncated JSON
    large_payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "echo " + ("A" * 70000) + " && rm -rf *.py"}})
    proto_cases = [
        ("large-64kb-block", large_payload, "B"),
        ("raw-non-json-block", "rm -rf *.py", "B"),
        ("truncated-json-block", '{"tool_name": "Bash", "tool_input": {"command": "rm -rf *.py', "B"),
        ("empty-stdin-pass", "", "P"),
        ("other-tool-pass", '{"tool_name": "Read", "tool_input": {"path": "rm -rf /"}}', "P"),
    ]
    runners = [("py", [sys.executable, "-B", str(PY_PATH)], False)]
    if has_ps:
        runners.append(("ps1", ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(PS1_PATH)], False))
    if bash_exe:
        runners.append(("sh", [bash_exe, str(SH_PATH)], False))
        # Also verify 64KB payload does NOT deadlock pure POSIX awk fallback
        checks += 1
        got = code_label(run_raw_stdin([bash_exe, str(SH_PATH)], large_payload, disable_py=True))
        if got != "B":
            failures += 1
            print(f"FAIL [sh-fallback/large-64kb] got={got} exp=B")

    for name, raw_in, exp in proto_cases:
        for rname, rcmd, dpy in runners:
            checks += 1
            got = code_label(run_raw_stdin(rcmd, raw_in, disable_py=dpy))
            if got != exp:
                failures += 1
                print(f"FAIL [{rname}/proto:{name}] got={got} exp={exp}")

    # 4. Pure shell fallback checks (GUARDRAIL_DISABLE_PYTHON=1)
    for cat, cmd, exp_ps, exp_sh in FALLBACK_CASES:
        if has_ps:
            checks += 1
            got = code_label(run_ps1(cmd, "stdin", disable_py=True))
            if got != exp_ps:
                failures += 1
                print(f"FAIL [ps1-fallback] [{cat}] got={got} exp={exp_ps} cmd={cmd!r}")
        if bash_exe:
            checks += 1
            got = code_label(run_sh(bash_exe, cmd, "stdin", disable_py=True))
            if got != exp_sh:
                failures += 1
                print(f"FAIL [sh-fallback]  [{cat}] got={got} exp={exp_sh} cmd={cmd!r}")

    print(f"\nVerified assertions: {checks} | Failures: {failures}")

    print("\n--- Documented Speed-Bump Bypass Baseline (informational) ---")
    for cmd in KNOWN_BYPASSES:
        py_r = code_label(run_py(cmd, "auto", "stdin"))
        ps_r = code_label(run_ps1(cmd, "stdin")) if has_ps else "-"
        sh_r = code_label(run_sh(bash_exe, cmd, "stdin")) if bash_exe else "-"
        print(f"  [KNOWN BYPASS] py={py_r} ps1={ps_r} sh={sh_r} | {cmd}")

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
