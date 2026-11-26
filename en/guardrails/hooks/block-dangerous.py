#!/usr/bin/env python3
"""
Cross-platform PreToolUse Hook - Destructive Command Speed Bump (Zero-Dependency Engine).

Inspects shell commands using a lightweight lexer (handling nested/escaped quotes,
comments, heredocs, command separators, subshells, and common wrappers) so everyday
commands (git commit messages, echo, grep, heredocs, Python/Node assertions, URLs)
pass cleanly while accidental destructive patterns exit with code 2.

Usage:
  Claude Code stdin JSON:
    python block-dangerous.py < payload.json
  Self-test:
    python block-dangerous.py --test "rm -rf *.py"
  Dialect hint (auto | ps | sh):
    python block-dangerous.py --dialect sh --test "rm -rf *.py"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass

if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8-sig", errors="replace")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


@dataclass
class Token:
    raw: str
    value: str
    quoted: bool = False
    is_op: bool = False


DANGEROUS_TARGETS = {
    "/", "//", "/*", "\\", "\\\\",
    ".", "./", ".\\", "..", "../", "..\\",
    "~", "~/", "~\\",
    "$home", "$home/", "$home\\", "${home}", "${home}/", "${home}\\",
    "$env:userprofile", "$env:userprofile\\", "$env:userprofile/",
    "$env:systemdrive", "$env:systemdrive\\", "$env:systemdrive/",
    "%userprofile%", "%userprofile%\\", "%systemdrive%", "%systemdrive%\\",
}

DRIVE_ROOT_RE = re.compile(r"^[a-zA-Z]:[\\/]?$")

NON_SQL_COMMANDS = {
    "echo", "printf", "write-output", "write-host", "write-verbose", "write-warning",
    "grep", "egrep", "fgrep", "rg", "ag", "ack", "select-string", "sls",
    "git", "curl", "wget", "invoke-webrequest", "iwr", "invoke-restmethod", "irm",
    "python", "python3", "py", "node", "deno", "bun", "ruby", "perl", "php",
    "pytest", "jest", "vitest", "mocha", "npm", "pnpm", "yarn", "npx",
    "cargo", "go", "rustc", "javac", "java", "mvn", "gradle",
    "cat", "head", "tail", "less", "more", "sed", "awk", "sort", "uniq", "wc", "tr", "cut",
    "cd", "pushd", "popd", "pwd", "ls", "dir", "get-childitem", "gci",
    "mkdir", "md", "touch", "cp", "copy", "copy-item", "mv", "move", "move-item",
    "test", "[", "[[", "true", "false", "export", "set", "unset", "alias",
}

SQL_DROP_RE = re.compile(r"\bDROP\s+(?:TABLE|DATABASE|SCHEMA)\b", re.IGNORECASE)
SQL_TRUNCATE_RE = re.compile(
    r"\bTRUNCATE\s+(?:TABLE\s+)?(?:ONLY\s+)?[`\"'\[]?[A-Za-z_][A-Za-z0-9_.$]*",
    re.IGNORECASE,
)

# Wrappers and how many option args consume a following value
WRAPPER_VALUE_FLAGS = {
    "sudo": {"-u", "-g", "-C", "-h", "-p", "-r", "-t", "-T", "-U", "--user", "--group", "--chdir"},
    "env": {"-u", "-C", "-S", "--unset", "--chdir", "--split-string"},
    "command": set(),
    "time": {"-f", "-o", "--format", "--output"},
    "nohup": set(),
    "exec": {"-a"},
}

GIT_GLOBAL_VALUE_FLAGS = {
    "-C", "-c", "--git-dir", "--work-tree", "--namespace", "--super-prefix",
    "--config-env", "--exec-path",
}

XARGS_VALUE_FLAGS = {
    "-a", "-d", "-E", "-e", "-I", "-L", "-l", "-n", "-P", "-s",
    "--arg-file", "--delimiter", "--eof", "--replace", "--max-lines",
    "--max-args", "--max-procs", "--max-chars",
}

CONTROL_KEYWORDS = {"if", "then", "elif", "else", "fi", "do", "done", "for", "while", "until", "case", "in", "!", "time"}


def extract_command(raw_stdin: str) -> str:
    """Extract command string from Claude Code JSON stdin or fall back safely."""
    raw_stdin = raw_stdin.lstrip("\ufeff")
    text = raw_stdin.strip()
    if not text:
        return ""
    try:
        obj = json.loads(raw_stdin)
    except json.JSONDecodeError:
        # Handle truncated/malformed JSON payloads containing a "command" field
        if text.startswith("{"):
            m = re.search(r'"command"\s*:\s*"((?:\\.|[^"\\])*)', raw_stdin, re.DOTALL)
            if m:
                frag = m.group(1)
                try:
                    return json.loads('"' + frag + '"')
                except Exception:
                    return frag.replace('\\"', '"').replace("\\n", "\n")
            return ""
        return raw_stdin

    if isinstance(obj, dict):
        tool_input = obj.get("tool_input")
        if isinstance(tool_input, dict) and isinstance(tool_input.get("command"), str):
            return tool_input["command"]
        if isinstance(obj.get("command"), str):
            return obj["command"]
    return ""


def strip_heredocs(text: str) -> str:
    """Replace heredoc bodies with empty lines so documentation/fixture content is not executed."""
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    heredoc_re = re.compile(r"<<-?\s*(?:'([^']+)'|\"([^\"]+)\"|([A-Za-z_][A-Za-z0-9_]*))")

    while i < len(lines):
        line = lines[i]
        out.append(line)
        # Only detect heredoc marker outside quotes on this line
        delimiters: list[tuple[str, bool]] = []
        in_sq = False
        in_dq = False
        j = 0
        while j < len(line):
            ch = line[j]
            if ch == "\\" and in_dq and j + 1 < len(line):
                j += 2
                continue
            if ch == "'" and not in_dq:
                in_sq = not in_sq
            elif ch == '"' and not in_sq:
                in_dq = not in_dq
            elif not in_sq and not in_dq:
                if ch == "#" and (j == 0 or line[j - 1].isspace()):
                    break
                if line[j : j + 2] == "<<" and (j + 2 >= len(line) or line[j + 2] != "<"):
                    m = heredoc_re.match(line, j)
                    if m:
                        delim = m.group(1) or m.group(2) or m.group(3)
                        strip_tabs = line[j : j + 3] == "<<-"
                        delimiters.append((delim, strip_tabs))
                        j = m.end()
                        continue
            j += 1

        i += 1
        for delim, strip_tabs in delimiters:
            while i < len(lines):
                candidate = lines[i].rstrip("\r\n")
                if strip_tabs:
                    candidate = candidate.lstrip("\t")
                i += 1
                if candidate == delim:
                    break
    return "".join(out)


def tokenize_shell(text: str, ps_mode: bool = False) -> tuple[list[list[Token]], list[str], list[str]]:
    """
    Tokenize shell command into segments separated by ;, &&, ||, |, newlines.
    Returns (segments, segment_separators_before, nested_subcommands).
    Properly handles single/double quotes (including multi-line), escapes, # comments,
    $(...) and backtick command substitutions, and subshell grouping () / {}.
    """
    segments: list[list[Token]] = []
    seps_before: list[str] = []
    nested: list[str] = []

    cur_seg: list[Token] = []
    cur_sep = ""
    buf_val: list[str] = []
    buf_raw: list[str] = []
    tok_quoted = False
    in_tok = False

    def flush_tok() -> None:
        nonlocal tok_quoted, in_tok
        if in_tok:
            cur_seg.append(Token(raw="".join(buf_raw), value="".join(buf_val), quoted=tok_quoted))
            buf_val.clear()
            buf_raw.clear()
            tok_quoted = False
            in_tok = False

    def flush_seg(next_sep: str) -> None:
        nonlocal cur_sep
        flush_tok()
        if cur_seg:
            segments.append(list(cur_seg))
            seps_before.append(cur_sep)
            cur_seg.clear()
        cur_sep = next_sep

    i = 0
    n = len(text)
    in_sq = False
    in_dq = False

    while i < n:
        ch = text[i]

        if in_sq:
            buf_raw.append(ch)
            if ps_mode and ch == "'" and i + 1 < n and text[i + 1] == "'":
                buf_val.append("'")
                buf_raw.append("'")
                i += 2
                continue
            if ch == "'":
                in_sq = False
            else:
                buf_val.append(ch)
            i += 1
            continue

        if in_dq:
            buf_raw.append(ch)
            if ch == "\\" and i + 1 < n and text[i + 1] in ('"', "\\", "$", "`", "\n"):
                nxt = text[i + 1]
                buf_raw.append(nxt)
                if nxt != "\n":
                    buf_val.append(nxt)
                i += 2
                continue
            if ps_mode and ch == "`" and i + 1 < n:
                nxt = text[i + 1]
                buf_raw.append(nxt)
                buf_val.append(nxt)
                i += 2
                continue
            if ch == '"':
                in_dq = False
                i += 1
                continue
            # Extract $(...) command substitution inside double quotes
            if ch == "$" and i + 1 < n and text[i + 1] == "(":
                sub, end_idx = _extract_balanced(text, i + 2, "(", ")")
                nested.append(sub)
                buf_val.append(text[i:end_idx])
                buf_raw.append(text[i + 1 : end_idx])
                i = end_idx
                continue
            if not ps_mode and ch == "`":
                end_idx = text.find("`", i + 1)
                if end_idx != -1:
                    nested.append(text[i + 1 : end_idx])
                    buf_val.append(text[i : end_idx + 1])
                    buf_raw.append(text[i + 1 : end_idx + 1])
                    i = end_idx + 1
                    continue
            buf_val.append(ch)
            i += 1
            continue

        # Outside quotes
        if ch in ("\r", "\n"):
            flush_seg("\n")
            i += 1
            continue

        if ch in (" ", "\t"):
            flush_tok()
            i += 1
            continue

        # Comment outside quotes at token boundary
        if ch == "#" and not in_tok:
            while i < n and text[i] not in ("\r", "\n"):
                i += 1
            continue

        # Backslash escape outside quotes (POSIX style; preserve Windows path backslashes in ps_mode)
        if not ps_mode and ch == "\\" and i + 1 < n:
            nxt = text[i + 1]
            if nxt == "\n":
                i += 2
                continue
            in_tok = True
            buf_raw.append(ch)
            buf_raw.append(nxt)
            buf_val.append(nxt)
            i += 2
            continue

        if ch == "'":
            in_sq = True
            in_tok = True
            tok_quoted = True
            buf_raw.append(ch)
            i += 1
            continue

        if ch == '"':
            in_dq = True
            in_tok = True
            tok_quoted = True
            buf_raw.append(ch)
            i += 1
            continue

        # Command substitution $(...)
        if ch == "$" and i + 1 < n and text[i + 1] == "(":
            sub, end_idx = _extract_balanced(text, i + 2, "(", ")")
            nested.append(sub)
            in_tok = True
            buf_val.append(text[i:end_idx])
            buf_raw.append(text[i:end_idx])
            i = end_idx
            continue

        # Backtick substitution (POSIX)
        if not ps_mode and ch == "`":
            end_idx = text.find("`", i + 1)
            if end_idx != -1:
                nested.append(text[i + 1 : end_idx])
                in_tok = True
                buf_val.append(text[i : end_idx + 1])
                buf_raw.append(text[i : end_idx + 1])
                i = end_idx + 1
                continue

        # Operators: &&, ||, ;, |
        if text[i : i + 2] in ("&&", "||"):
            flush_seg(text[i : i + 2])
            i += 2
            continue

        if ch in (";", "|"):
            flush_seg(ch)
            i += 1
            continue

        # PowerShell call operator `& cmd` at start of segment vs background `&`
        if ch == "&":
            if not cur_seg and not in_tok:
                # Keep `&` as leading operator token so strip_wrappers removes it
                cur_seg.append(Token(raw="&", value="&", is_op=True))
                i += 1
                continue
            # Preserve redirections like 2>&1 or >&2
            if (in_tok and buf_val and buf_val[-1] == ">") or (i + 1 < n and text[i + 1] == ">"):
                in_tok = True
                buf_raw.append(ch)
                buf_val.append(ch)
                i += 1
                continue
            flush_seg("&")
            i += 1
            continue

        # Subshell grouping `(...)` at segment start
        if ch == "(" and not cur_seg and not in_tok:
            sub, end_idx = _extract_balanced(text, i + 1, "(", ")")
            nested.append(sub)
            i = end_idx
            continue

        # Brace group `{ ...; }` at segment start (POSIX) or PS scriptblock `{ ... }`
        if ch == "{" and not in_tok:
            sub, end_idx = _extract_balanced(text, i + 1, "{", "}")
            if not cur_seg:
                nested.append(sub)
            else:
                # Keep scriptblock as a token (e.g., ForEach-Object { Remove-Item $_ })
                cur_seg.append(Token(raw="{" + sub + "}", value=sub))
            i = end_idx
            continue

        in_tok = True
        buf_raw.append(ch)
        buf_val.append(ch)
        i += 1

    flush_seg("")
    return segments, seps_before, nested


def _extract_balanced(text: str, start: int, open_ch: str, close_ch: str) -> tuple[str, int]:
    """Extract content inside balanced delimiters starting just after open_ch."""
    depth = 1
    i = start
    n = len(text)
    in_sq = False
    in_dq = False
    while i < n and depth > 0:
        ch = text[i]
        if ch == "\\" and in_dq and i + 1 < n:
            i += 2
            continue
        if ch == "'" and not in_dq:
            in_sq = not in_sq
        elif ch == '"' and not in_sq:
            in_dq = not in_dq
        elif not in_sq and not in_dq:
            if ch == open_ch:
                depth += 1
            elif ch == close_ch:
                depth -= 1
                if depth == 0:
                    return text[start:i], i + 1
        i += 1
    return text[start:n], n


def normalize_cmd_name(token: str) -> str:
    """Normalize command executable name: strip path prefix, backslashes, and .exe/.cmd/.bat."""
    name = token.strip()
    if "/" in name or "\\" in name:
        # Handle /bin/rm, C:\Windows\System32\cmd.exe, and r\m escapes
        if re.match(r"^(?:[a-zA-Z]:|\.{1,2}[\\/]|[\\/])", name) or "/" in name:
            name = re.split(r"[\\/]", name)[-1]
        else:
            name = name.replace("\\", "")
    low = name.lower()
    for ext in (".exe", ".cmd", ".bat"):
        if low.endswith(ext) and len(low) > len(ext):
            low = low[: -len(ext)]
            break
    return low


def strip_prefixes(tokens: list[Token]) -> list[Token]:
    """Strip leading env assignments, control keywords, call operator &, and wrappers."""
    idx = 0
    n = len(tokens)
    env_re = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")

    while idx < n:
        val = tokens[idx].value
        low = normalize_cmd_name(val)

        if val == "&" and tokens[idx].is_op:
            idx += 1
            continue
        if not tokens[idx].quoted and env_re.match(val):
            idx += 1
            continue
        if not tokens[idx].quoted and low in CONTROL_KEYWORDS:
            # Skip `for x in ...` header tokens up to next segment, or simple prefix like `then`/`do`
            if low in ("for", "case"):
                return []
            idx += 1
            continue
        if low in WRAPPER_VALUE_FLAGS:
            val_flags = WRAPPER_VALUE_FLAGS[low]
            idx += 1
            while idx < n:
                arg = tokens[idx].value
                if arg == "--":
                    idx += 1
                    break
                if arg.startswith("-") and len(arg) > 1:
                    idx += 1
                    if arg in val_flags and idx < n:
                        idx += 1
                    continue
                if low == "env" and env_re.match(arg):
                    idx += 1
                    continue
                break
            continue
        if low == "timeout":
            idx += 1
            # Skip timeout flags and duration argument
            while idx < n and tokens[idx].value.startswith("-"):
                flag = tokens[idx].value
                idx += 1
                if flag in ("-k", "-s", "--kill-after", "--signal") and idx < n:
                    idx += 1
            if idx < n:
                idx += 1  # duration
            continue
        break

    return tokens[idx:]


def is_dangerous_target(path: str) -> bool:
    """Return True if path points to root, drive root, home dir, cwd, or parent dir."""
    p = path.strip()
    if not p:
        return False
    low = p.lower()
    if low in DANGEROUS_TARGETS:
        return True
    if DRIVE_ROOT_RE.match(p):
        return True
    # Multiple slashes like /// or \\\
    if set(p) <= {"/", "\\"}:
        return True
    return False


def is_ps_recurse_flag(arg: str) -> bool:
    low = arg.lower()
    if low in ("-r", "-re", "-rec", "-recu", "-recur", "-recurs", "-recurse"):
        return True
    return False


def check_segment(
    tokens: list[Token],
    sep_before: str,
    dialect: str,
    depth: int,
) -> str | None:
    """Inspect a single normalized command segment. Return block reason or None."""
    norm = strip_prefixes(tokens)
    if not norm:
        return None

    cmd = normalize_cmd_name(norm[0].value)
    args = norm[1:]
    arg_vals = [t.value for t in args]
    ps_enabled = dialect in ("ps", "auto")

    # 1. Pipeline into PowerShell delete cmdlets or ForEach-Object { Remove-Item ... }
    if sep_before == "|" and ps_enabled:
        if cmd in ("remove-item", "ri", "del", "erase", "rd", "rmdir"):
            return "pipeline-remove-item"
        if cmd in ("foreach-object", "foreach", "%"):
            joined_sb = " ".join(arg_vals)
            if re.search(r"(?i)\b(Remove-Item|ri|del|erase|rm)\b", joined_sb):
                return "pipeline-remove-item"

    # 2. Inline shell wrappers: bash -c / sh -c / eval / powershell -c / cmd /c
    if depth < 3:
        inner_cmds: list[tuple[str, str]] = []
        if cmd in ("sh", "bash", "zsh", "dash", "ksh"):
            for i, a in enumerate(arg_vals):
                if a in ("-c", "-lc", "-ec") and i + 1 < len(arg_vals):
                    inner_cmds.append((arg_vals[i + 1], "sh"))
                    break
        elif cmd == "eval" and arg_vals:
            inner_cmds.append((" ".join(arg_vals), "sh"))
        elif cmd in ("powershell", "pwsh"):
            for i, a in enumerate(arg_vals):
                low_a = a.lower()
                if low_a in ("-c", "-co", "-com", "-comm", "-comma", "-comman", "-command") and i + 1 < len(arg_vals):
                    inner_cmds.append((" ".join(arg_vals[i + 1 :]), "ps"))
                    break
        elif cmd == "cmd":
            for i, a in enumerate(arg_vals):
                if a.lower() in ("/c", "/k") and i + 1 < len(arg_vals):
                    inner_cmds.append((" ".join(arg_vals[i + 1 :]), "ps"))
                    break
        for inner_cmd, inner_dialect in inner_cmds:
            reason = inspect_command(inner_cmd, dialect=inner_dialect, depth=depth + 1)
            if reason:
                return reason

    # 3. Delete commands: rm / rmdir / Remove-Item / ri / del / erase / rd
    delete_cmds = {"rm", "rmdir", "shred"}
    if ps_enabled:
        delete_cmds |= {"remove-item", "ri", "del", "erase", "rd"}

    if cmd in delete_cmds:
        has_recurse = False
        is_literal_path = False
        after_dd = False
        targets: list[Token] = []
        i = 0
        while i < len(args):
            t = args[i]
            v = t.value
            low = v.lower()
            if not after_dd and v == "--":
                after_dd = True
                i += 1
                continue
            if not after_dd and not t.quoted:
                # CMD switches like /s /q /f
                if cmd in ("rd", "rmdir", "del", "erase") and re.match(r"^/[a-zA-Z]$", v):
                    if low == "/s":
                        has_recurse = True
                    i += 1
                    continue
                if low in ("-literalpath", "-lp"):
                    is_literal_path = True
                    i += 1
                    if i < len(args):
                        targets.append(args[i])
                        i += 1
                    continue
                if low in ("-path",):
                    i += 1
                    if i < len(args):
                        targets.append(args[i])
                        i += 1
                    continue
                if is_ps_recurse_flag(v) or low == "--recursive":
                    has_recurse = True
                    i += 1
                    continue
                if v.startswith("--"):
                    if low in ("--recursive",):
                        has_recurse = True
                    i += 1
                    continue
                if v.startswith("-") and len(v) > 1:
                    # Short flag bundle like -rf, -fr, -r, -R, -fo
                    if "r" in low[1:]:
                        has_recurse = True
                    i += 1
                    continue
            targets.append(t)
            i += 1

        # Check wildcard deletion across targets
        if not is_literal_path:
            for t in targets:
                if "*" in t.value or "?" in t.value:
                    return "wildcard-delete"

        # Check recursive root/home/cwd/parent wipe
        if has_recurse:
            for t in targets:
                if is_dangerous_target(t.value):
                    return "recurse-root" if cmd in ("remove-item", "ri", "rd", "rmdir", "del", "erase") and ps_enabled else "rm-root-or-cwd"

    # 4. find -delete / find -exec rm / find -execdir rm
    if cmd == "find":
        for i, a in enumerate(arg_vals):
            if a == "-delete":
                return "find-delete"
            if a in ("-exec", "-execdir") and i + 1 < len(arg_vals):
                exec_cmd = normalize_cmd_name(arg_vals[i + 1])
                if exec_cmd in ("rm", "rmdir", "remove-item", "del", "erase"):
                    return "find-delete"

    # 5. xargs rm (check only the actual target command executed by xargs)
    if cmd == "xargs":
        i = 0
        while i < len(arg_vals):
            a = arg_vals[i]
            if a == "--":
                i += 1
                break
            if a.startswith("-") and len(a) > 1:
                i += 1
                if a in XARGS_VALUE_FLAGS and i < len(arg_vals):
                    i += 1
                continue
            break
        if i < len(arg_vals):
            target_cmd = normalize_cmd_name(arg_vals[i])
            if target_cmd in ("rm", "rmdir", "remove-item", "del", "erase"):
                return "xargs-rm"

    # 6. Destructive Git (skip global git flags like -C, -c, --no-pager, --git-dir)
    if cmd == "git":
        i = 0
        while i < len(arg_vals):
            a = arg_vals[i]
            if a in GIT_GLOBAL_VALUE_FLAGS:
                i += 2
                continue
            if a.startswith("-"):
                i += 1
                continue
            break
        if i < len(arg_vals):
            sub = arg_vals[i].lower()
            sargs = arg_vals[i + 1 :]
            if sub == "reset" and any(a == "--hard" for a in sargs):
                return "git-reset-hard"
            if sub == "clean":
                is_dry = any(a in ("-n", "--dry-run") or (a.startswith("-") and not a.startswith("--") and "n" in a[1:]) for a in sargs)
                has_f = any(a == "--force" or (a.startswith("-") and not a.startswith("--") and "f" in a[1:]) for a in sargs)
                if has_f and not is_dry:
                    return "git-clean-force"
            if sub == "push":
                for a in sargs:
                    if a in ("--force", "--force=true", "--mirror"):
                        return "git-push-force"
                    if a.startswith("-") and not a.startswith("--") and "f" in a[1:]:
                        return "git-push-force"
            if sub in ("checkout", "restore"):
                # Inspect path arguments for `.`, `./`, `.\`
                for a in sargs:
                    if a in (".", "./", ".\\"):
                        return "git-discard-all"
            if sub == "stash" and sargs and sargs[0].lower() in ("clear", "drop"):
                return "git-stash-drop"
            if sub == "branch" and any(a == "-D" for a in sargs):
                return "git-branch-force-delete"

    # 7. Destructive IaC (terraform / tofu)
    if cmd in ("terraform", "tofu") and arg_vals:
        sub = arg_vals[0].lower()
        if sub == "destroy":
            return "terraform-destroy"
        if sub == "apply" and any(a in ("-destroy", "--destroy") for a in arg_vals[1:]):
            return "terraform-destroy"

    # 8. Disk wipe / format / chmod -R /
    if cmd.startswith("mkfs"):
        return "disk-format"
    if cmd == "format" and any(DRIVE_ROOT_RE.match(a) for a in arg_vals):
        return "disk-format"
    if cmd == "dd" and any(a.lower().startswith("of=/dev/") for a in arg_vals):
        return "disk-wipe"
    if cmd == "chmod":
        has_r = any(a in ("-R", "--recursive") or (a.startswith("-") and not a.startswith("--") and "R" in a[1:]) for a in arg_vals)
        if has_r and any(a in ("/", "/*") for a in arg_vals):
            return "chmod-root"

    # 9. Destructive SQL (evaluated strictly per-segment, skipping non-SQL commands)
    if cmd not in NON_SQL_COMMANDS:
        # Special case: docker/kubectl exec wrapping psql/mysql or direct SQL client / raw SQL
        seg_text = " ".join(t.value for t in norm)
        if SQL_DROP_RE.search(seg_text):
            return "sql-drop"
        if SQL_TRUNCATE_RE.search(seg_text):
            return "sql-truncate"

    return None


def inspect_command(cmd: str, dialect: str = "auto", depth: int = 0) -> str | None:
    """Analyze a full command string and return the first matched block reason, or None."""
    if not cmd:
        return None
    cmd = cmd.lstrip("\ufeff")
    if not cmd.strip():
        return None
    ps_mode = dialect == "ps"
    cleaned = strip_heredocs(cmd)
    segments, seps_before, nested = tokenize_shell(cleaned, ps_mode=ps_mode)

    for seg, sep in zip(segments, seps_before):
        reason = check_segment(seg, sep, dialect=dialect, depth=depth)
        if reason:
            return reason

    if depth < 3:
        for sub in nested:
            reason = inspect_command(sub, dialect=dialect, depth=depth + 1)
            if reason:
                return reason

    return None


def block_now(reason: str, original_cmd: str) -> int:
    preview = original_cmd if len(original_cmd) <= 300 else original_cmd[:300] + "... (truncated)"
    sys.stderr.write(f"BLOCKED BY GUARDRAIL: Destructive or wildcard command blocked ({reason})\n")
    sys.stderr.write(f"Command: {preview}\n")
    sys.stderr.write(
        "Safe alternative: Move unwanted files to _trash_box/ via exact paths, "
        "or recover via git stash / git revert.\n"
    )
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PreToolUse destructive command speed-bump hook.")
    parser.add_argument("--test", dest="test_cmd", default=None, help="Directly test a command string.")
    parser.add_argument(
        "--dialect",
        choices=("auto", "ps", "sh"),
        default="auto",
        help="Shell dialect hint (default: auto).",
    )
    args = parser.parse_args(argv)

    if args.test_cmd is not None:
        cmd = args.test_cmd
    else:
        raw = sys.stdin.read()
        cmd = extract_command(raw)

    reason = inspect_command(cmd, dialect=args.dialect)
    if reason:
        return block_now(reason, cmd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
