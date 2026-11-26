#!/usr/bin/env bash
# PreToolUse (Bash) Hook - Destructive Command Speed Bump
#
# Delegates to the sibling zero-dependency Python lexer engine (block-dangerous.py)
# when python3/python is available (fast, quote/heredoc/multi-line safe, no 64KB
# pipe deadlock). Falls back to a portable POSIX awk engine (BSD & GNU compatible)
# when Python is unavailable.
#
# Exit codes: 2 = blocked (reason written to stderr), 0 = allowed.
# Self-test:  bash block-dangerous.sh --test "rm -rf *.py"

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PY_ENGINE="$SCRIPT_DIR/block-dangerous.py"

# Fast path: delegate to sibling Python engine when available (unless disabled for fallback tests)
if [[ "${GUARDRAIL_DISABLE_PYTHON:-0}" != "1" ]] && [[ -f "$PY_ENGINE" ]]; then
  PY_BIN=""
  if command -v python3 >/dev/null 2>&1; then
    PY_BIN="python3"
  elif command -v python >/dev/null 2>&1; then
    PY_BIN="python"
  fi
  if [[ -n "$PY_BIN" ]]; then
    if [[ "${1:-}" == "--test" ]]; then
      exec "$PY_BIN" -B "$PY_ENGINE" --dialect sh --test "${2:-}"
    else
      exec "$PY_BIN" -B "$PY_ENGINE" --dialect sh
    fi
  fi
fi

# Portable fallback path (no Python): uses jq + POSIX awk (works on both macOS BSD and GNU)
CMD=""
if [[ "${1:-}" == "--test" ]]; then
  CMD="${2:-}"
else
  RAW_INPUT="$(cat)"
  if command -v jq >/dev/null 2>&1; then
    CMD="$(printf '%s' "$RAW_INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null || true)"
    if [[ -z "$CMD" ]] && [[ "$RAW_INPUT" != \{* ]]; then
      CMD="$RAW_INPUT"
    fi
  else
    # Basic POSIX awk extraction for JSON {"tool_input":{"command":"..."}} or raw command
    CMD="$(printf '%s' "$RAW_INPUT" | awk '
      BEGIN { RS = "\0"; text = "" }
      { text = text $0 }
      END {
        if (text ~ /^[[:space:]]*\{/) {
          if (match(text, /"command"[[:space:]]*:[[:space:]]*"([^"\\]|\\.)*"/)) {
            s = substr(text, RSTART, RLENGTH)
            sub(/^"command"[[:space:]]*:[[:space:]]*"/, "", s)
            sub(/"$/, "", s)
            gsub(/\\"/, "\"", s)
            gsub(/\\n/, "\n", s)
            print s
          }
        } else {
          print text
        }
      }
    ')"
  fi
fi

[[ -z "$CMD" ]] && exit 0

# Stream command via pipe (never <<< here-string, avoiding MSYS2 64KB deadlock) into POSIX awk
REASON="$(printf '%s\n' "$CMD" | awk '
  function strip_quotes(s,   out, i, c, in_sq, in_dq, n) {
    out = ""; in_sq = 0; in_dq = 0; n = length(s)
    for (i = 1; i <= n; i++) {
      c = substr(s, i, 1)
      if (in_sq) {
        if (c == "\047") { in_sq = 0; out = out "\047" }
      } else if (in_dq) {
        if (c == "\\" && i < n) { i++; continue }
        if (c == "\"") { in_dq = 0; out = out "\"" }
      } else {
        if (c == "\047") { in_sq = 1; out = out "\047" }
        else if (c == "\"") { in_dq = 1; out = out "\"" }
        else if (c == "#" && (i == 1 || substr(s, i - 1, 1) ~ /[[:space:]]/)) { break }
        else { out = out c }
      }
    }
    return out
  }

  function trim_prefix(s) {
    sub(/^[[:space:]]+/, "", s)
    while (s ~ /^([A-Za-z_][A-Za-z0-9_]*=[^[:space:]]+[[:space:]]+|(sudo|env|command|time|nohup)[[:space:]]+)/) {
      sub(/^([A-Za-z_][A-Za-z0-9_]*=[^[:space:]]+[[:space:]]+|(sudo|env|command|time|nohup)[[:space:]]+)/, "", s)
      sub(/^[[:space:]]+/, "", s)
    }
    return s
  }

  function check_seg(raw_seg, clean_seg,   norm, low, rlow) {
    norm = trim_prefix(clean_seg)
    if (norm == "") return ""
    low = tolower(norm)
    rlow = tolower(trim_prefix(raw_seg))

    if (low ~ /^(rm|rmdir)[[:space:]]+.*(\*|\?)/) return "wildcard-delete"
    if (rlow ~ /^(rm|rmdir)[[:space:]]+.*["\047][^"\047]*(\*|\?)[^"\047]*["\047]/) return "wildcard-delete"
    if (low ~ /^rm[[:space:]]+.*-[a-z]*[rf][a-z]*[[:space:]]+(\/|~\/?|\$home\/?|\.\.?[\/\\]?)([[:space:]]|$)/) return "rm-root-or-cwd"
    if (rlow ~ /^rm[[:space:]]+.*-[a-z]*[rf][a-z]*[[:space:]]+["\047](\/|~\/?|\$home\/?|\.\.?[\/\\]?)["\047]([[:space:]]|$)/) return "rm-root-or-cwd"
    if (low ~ /^find[[:space:]]+.*([[:space:]]-delete([[:space:]]|$)|[[:space:]]-exec(dir)?[[:space:]]+([^[:space:]]*\/)?rm([[:space:]]|$))/) return "find-delete"
    if (low ~ /^xargs[[:space:]]+((-[^[:space:]]+[[:space:]]+)*)([^[:space:]]*\/)?rm([[:space:]]|$)/) return "xargs-rm"
    if (low ~ /^git[[:space:]]+((-[cC][[:space:]]+[^[:space:]]+[[:space:]]+|--[a-z-]+(=[^[:space:]]+)?[[:space:]]+)*)reset[[:space:]]+.*--hard([[:space:]]|$)/) return "git-reset-hard"
    if (low ~ /^git[[:space:]]+((-[cC][[:space:]]+[^[:space:]]+[[:space:]]+|--[a-z-]+(=[^[:space:]]+)?[[:space:]]+)*)clean[[:space:]]+.*([[:space:]]-[a-z]*f|[[:space:]]--force([[:space:]]|$))/) return "git-clean-force"
    if (low ~ /^git[[:space:]]+((-[cC][[:space:]]+[^[:space:]]+[[:space:]]+|--[a-z-]+(=[^[:space:]]+)?[[:space:]]+)*)push([[:space:]]+.*)?[[:space:]]+(--force(=true)?|--mirror|-[a-z]*f[a-z]*)([[:space:]]|$)/) return "git-push-force"
    if (low ~ /^git[[:space:]]+((-[cC][[:space:]]+[^[:space:]]+[[:space:]]+|--[a-z-]+(=[^[:space:]]+)?[[:space:]]+)*)(checkout|restore)[[:space:]]+.*[[:space:]]\.[\/\\]?([[:space:]]|$)/) return "git-discard-all"
    if (low ~ /^git[[:space:]]+((-[cC][[:space:]]+[^[:space:]]+[[:space:]]+|--[a-z-]+(=[^[:space:]]+)?[[:space:]]+)*)stash[[:space:]]+(clear|drop)([[:space:]]|$)/) return "git-stash-drop"
    if (low ~ /^(terraform|tofu)[[:space:]]+(destroy([[:space:]]|$)|apply[[:space:]]+.*--?destroy([[:space:]]|$))/) return "terraform-destroy"

    if (low !~ /^(echo|printf|grep|egrep|fgrep|rg|git|curl|wget|python|python3|node|pytest|cd|cat)([[:space:]]|$)/) {
      if (rlow ~ /(^|[^a-z0-9_])drop[[:space:]]+(table|database|schema)([^a-z0-9_]|$)/) return "sql-drop"
      if (rlow ~ /(^|[^a-z0-9_])truncate[[:space:]]+(table[[:space:]]+)?[a-z_"`\[]/) return "sql-truncate"
    }
    return ""
  }

  {
    sub(/\r$/, "")
    if ($0 ~ /^[[:space:]]*$/) next
    cl = strip_quotes($0)
    # Split on &&, ||, ;, | using portable awk gsub
    raw_tmp = $0
    cl_tmp = cl
    gsub(/&&|\|\||[;|]/, "\037", cl_tmp)
    gsub(/&&|\|\||[;|]/, "\037", raw_tmp)
    n_cl = split(cl_tmp, cl_segs, "\037")
    n_raw = split(raw_tmp, raw_segs, "\037")
    for (k = 1; k <= n_cl; k++) {
      rseg = (k <= n_raw ? raw_segs[k] : "")
      reason = check_seg(rseg, cl_segs[k])
      if (reason != "") {
        print reason
        exit 0
      }
    }
  }
')"

if [[ -n "$REASON" ]]; then
  {
    echo "BLOCKED BY GUARDRAIL: Destructive or wildcard command blocked ($REASON)"
    echo "Command: ${CMD:0:300}"
    echo "Safe alternative: Move unwanted files to _trash_box/ using exact paths, or recover via git stash / git revert."
  } >&2
  exit 2
fi

exit 0
