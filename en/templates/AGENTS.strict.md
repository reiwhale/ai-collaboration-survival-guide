# AGENTS.md · Frontier Audit & Heavy Engineering Edition (Strict)

> ⚠️ **Model Threshold Notice**: This ruleset enforces 5-tier evidence tagging and adversarial self-checks.  
> **Recommended ONLY for frontier reasoning models (e.g., Claude Opus / Sonnet, Gemini Pro, flagship GPT).**  
> For `Flash / Mini / Haiku` or `DeepSeek-V4.1-Flash`, switch back to `AGENTS.lite.md` to avoid rule-overload paralysis.

## 1. Host Environment Self-Portrait (Skip If Present · Read-Only Safe · `/sync-env`)

- **First Run**: Check if `.agent-env.local.txt` exists in the workspace root:
  - **Writable projects**: Confirm `.gitignore` lists `.agent-env.local.txt` and `_trash_box/` first (add them if missing), then execute `python scripts/probe_env.py` (or minimal read-only OS/shell commands) to capture OS, shell, locale encoding, CLI versions, and platform traps.
  - **Read-only / audit sessions**: Keep the workspace untouched; run `--dry-run` to stdout or redirect `--output` outside the repo.
- **Reuse & Refresh**: Reuse existing `.agent-env.local.txt` without re-scanning. Only refresh on **`/sync-env`** or **`sync local environment`** and report the diff.
- **Privacy Red Line**: Never touch `.env`, credentials, tokens, or unrelated personal directories.

## 2. Intent Alignment, Doc Freshness & Safety Brakes

1. **Sentence-Level Intent Gate**: Questions and exploratory thoughts remain strictly read-only. Before multi-file edits, renames, or removals, present a 4-column plan (`Path | Before -> After | Reason | Blast Radius`) and await confirmation.
2. **Document Freshness Audit (Code > Docs)**: Whenever a doc looks inconsistent with live code, errors, or folder layout, compare its last-modified time against recent code commits. Outdated docs drop to `[Reference]`—verify against live code first before trusting or updating.
3. **Safety Net & 2-Strike Circuit Breaker**: Verify a clean Git checkpoint before sweeping edits; stage removals inside `_trash_box/` until stabilized. Never execute `git reset --hard`, wildcard deletion (`*` / `?`), force pushes, or in-place patching of corrupted files (save `.broken` and rebuild from clean source). **After 2 consecutive fix attempts on the same bug that yield no new diagnostic info**, halt and recover via `git stash` / `git revert`.
4. **Verbatim Identifiers & Secret Isolation**: Copy all paths, keys, IDs, and git hashes verbatim from authoritative sources. Never read or echo real `.env` secrets or production credentials.

## 3. Five Evidence Levels & Verification Loop

Tag factual claims by their weakest supporting link (weakest-link rule):  
`[Observed]` (verified command output or file readback in this session) / `[Declared]` (config or docs claim, unverified at runtime) / `[Inferred]` / `[Self-Reported]` / `[Reference]`.

1. **Read Back Writes & Re-Run Full Baseline**: Tool success messages are not proof. Read back modified files and re-run the entire pre-edit baseline check after any fix.
2. **Defeat Fence-Error False Negatives**: Whenever a search or validator returns "0 matches / clean", run an accompanying **positive control probe guaranteed to trigger**, and rule out output truncation, multi-frame containers (e.g., zstd per-record frames), or CRLF/encoding mismatches. If the control fails, report `Validator Broken`.
3. **3-Part Delivery Report** (never say "All Passed!", and never equate mock unit tests with real-world validation):
   - **Verified Coverage**: exact checks + commands + measured outputs (specify Mock vs Real environment);
   - **Uncovered Scope (Required)**: platforms, real-user flows, or assumptions not tested;
   - **Conclusion & Risks**: restrained verdict grounded in the above.

## 4. Hot / Cold Knowledge Evolution Gate

- Cap this hot `AGENTS.md` at **80 lines / 5.5 KB**. Append new project-specific lessons into cold `docs/lessons.md` first (never auto-injected).
- Promote only cross-module bugs repeating **>= 2 times**. At **90% capacity (~72 lines / ~5 KB)**, every addition must evict equivalent volume back to the cold layer.
