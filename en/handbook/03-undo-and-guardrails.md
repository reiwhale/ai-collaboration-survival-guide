# Lesson 3 · Undo Safety Nets & Blocking Accidental Wipes

> Probabilistic models will never run 100% of commands without mistakes. Real safety is not praying for perfection—it is **keeping undo costs near zero and adding a speed bump against accidental wipes**.

---

## 1. Beginner Git Safety Net (No `&&` Chaining)

- Keep this cross-platform cheatsheet handy (Windows PowerShell 5.1, macOS zsh, and Linux bash): [`../guardrails/git-safety-cheatsheet.md`](../guardrails/git-safety-cheatsheet.md)
- Three essentials:
  1. Before big edits: `git add -A` then `git commit -m "checkpoint"`;
  2. Broke uncommitted code: `git stash push -u -m "broken"` (recover later with `git stash apply` / `pop`; **never `git reset --hard`**);
  3. Already committed a buggy change: `git revert HEAD --no-edit`.

---

## 2. Speed-Bump Hooks + Reversible `_trash_box/` Staging

- **Terminal speed bump**: Markdown warnings fade after context compaction. On **Claude Code**, you can wire [`../guardrails/hooks/README.md`](../guardrails/hooks/README.md) so common wildcard wipes (`rm -rf *.py`, `rm *.py`), `reset --hard`, and `DROP TABLE` exit with `exit 2`.
  - ⚠️ **Honest boundary**: Regex hooks are only a **first-line speed bump** (they cannot stop equivalent bypasses like `rm -rf src` or `python -c` deletions). **Git checkpoints + your IDE/CLI's native approval prompt remain your true safety net.**
- **Reversible cleanup**: During refactors, move obsolete files into `.gitignore`-d **`_trash_box/`**. Once the new version runs stably for a day or two, delete `_trash_box/` cleanly in one click.

---

## 3. Emergency Recovery If Files Were Scrambled Without Git

Golden rule: **Once a file is truncated or corrupted by an AI, NEVER let it patch that broken file by line numbers**—offsets computed against broken text chop away surviving sections.

Save the damaged file as `.broken` first, then recover in this **everyday priority order**:
1. **Your IDE's Built-In Local History (Fastest — saves 90% of no-Git mishaps)**:
   - **VS Code / Cursor**: Open the **Timeline** panel at the bottom of the Explorer sidebar, select the damaged file, and restore the snapshot from right before the AI edit.
   - **JetBrains IDEs (PyCharm / IntelliJ / WebStorm)**: Right-click the file or folder -> **Local History -> Show History**, compare, and revert cleanly.
2. **OS Trash / Cloud Sync Version History**: Check Recycle Bin / Trash or OneDrive / iCloud / Dropbox version history.
3. **Forensic Log Recovery (Last Resort)**: If neither Git nor IDE history exists, follow the advanced session-log recovery checklist in [Lesson 5](05-advanced-audit-and-incidents.md), or rebuild explicitly labeled `[Reconstructed - Not Original]`.
