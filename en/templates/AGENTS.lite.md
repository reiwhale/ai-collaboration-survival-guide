# AGENTS.md · Lean Survival Rules (Lite)

> Goal: Four zero-friction guardrails to stop accidental wipes, blind fix loops, and hallucinated fixes—without slowing down everyday coding.

1. **Separate Questions from Edits; Confirm High-Risk Changes**  
   Questions (*"is it / why / should we"*) stay strictly read-only. **Execute clear, routine edits that Git can undo in one step directly.** Pause to present the plan and blast radius before **irreversible actions (deleting untracked files, wiping databases, mutating external services, force-pushing remotes)**, **sweeping edits in repos without Git**, or **major architectural / ambiguous changes**. When clarifying ambiguity or awaiting a decision, prefer the host's native multiple-choice question tool; in plain terminals, offer 2–4 `A/B/C` options with a recommended pick and a one-line plain explanation.
2. **Make Mistakes Painless: Checkpoints + 2-Strike Breaker**  
   Confirm a clean Git commit exists before sweeping changes (prompt `git init` if missing). Stage obsolete files inside `_trash_box/` (verify `.gitignore` ignores it first) instead of running wildcard deletes (`rm -rf *`, `*.py`) or `git reset --hard`. **If 2 consecutive fix attempts on the same error yield no new diagnostic info, stop immediately** and suggest rolling back via `git stash` / `git revert`.
3. **Report Only Verified Facts; Admit Unknowns**  
   Copy paths and symbols verbatim from source—never invent APIs, and verify scan scope before claiming *"not found"*. **Whenever files or configs were modified**, end briefly with: **files changed · exact test command & outcome · uncovered scope** (mock tests do not replace real-app checks).
4. **Live Code > Stale Docs; Keep New Traps Cold**  
   Treat untouched docs as reference only and verify against live source code. Log project-specific traps in cold `docs/lessons.md` rather than bloating this file. If `scripts/probe_env.py` is present, run it on OS/toolchain errors or `/sync-env` to refresh the local host profile.
