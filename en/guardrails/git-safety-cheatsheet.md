# Git Undo Cheatsheet (Cross-Platform · Beginner Safe)

> Never rely on chat history or `Ctrl+Z` to undo multi-file AI edits.  
> Every command below is split onto **separate lines (no `&&`)**, so it runs cleanly on **Windows PowerShell 5.1, macOS zsh, and Linux bash**.

---

## Know These 3 Separate Concepts First

1. **Git Staging Index**: Changes queued by `git add` awaiting commit.
2. **`git stash` (Emergency Drawer)**: Packs away **uncommitted** messy edits so your workspace returns to the last clean commit—nothing is permanently destroyed.
3. **`_trash_box/` (Local Disposal Bin)**: A `.gitignore`-d folder inside your project where AI moves deprecated files until you verify stability and delete the folder yourself.

---

## 0. Before Starting: Does Your Project Have Save Slots?

Run inside your project directory:
```text
git status
```
If it says `not a git repository`, initialize your baseline safety net first (set local identity on lines 2–3 if this is a brand-new Git install, otherwise `commit` will refuse):
```text
git init
git config user.name "Your Name"
git config user.email "you@example.com"
git add .
git commit -m "chore: initial baseline"
```

---

## 1. The 3 Essential Safety Commands

### ① Save Before Asking AI for Big Edits
```text
git add -A
git commit -m "checkpoint: before AI edit"
```

### ② Inspect What AI Actually Touched
```text
git status -s
git diff --stat
```
View exact line-by-line changes:
```text
git diff
```

### ③ Roll Back When AI Breaks Your App

- **Case A (Not yet committed — broke right now) -> Pack into Stash**:
  ```text
  git stash push -u -m "broken-ai-attempt"
  ```
  > To inspect or bring back stashed code later:
  > ```text
  > git stash list          # List saved drawer entries (e.g., stash@{0})
  > git stash apply         # Restore latest stash while keeping a backup copy (safest)
  > git stash pop           # Restore latest stash and remove it from the drawer
  > ```
  > **Never blindly run `git reset --hard`**, which wipes uncommitted edits irreversibly.

- **Case B (Already committed a broken change) -> Safe Reverse Commit**:
  ```text
  git revert HEAD --no-edit
  ```
  > `git revert` creates a new commit that cleanly undoes the faulty commit **without rewriting or destroying Git history**.

---

## 2. Branch Isolation, 2-Strike Breaker & `_trash_box/`

- **Branch isolation**: Before major refactors, run `git switch -c feat/ai-experiment`. Merge if it works; discard the branch cleanly if it blows up.
- **2-Strike Breaker**: If 2 consecutive fix attempts on the same error produce **no new diagnostic info**, stop and run `git stash push -u -m "stop-loss"`.
- **Clean `_trash_box/` once stable**: Move dead scripts to `_trash_box/` during refactoring; delete that single folder once everything runs smoothly for a day.
