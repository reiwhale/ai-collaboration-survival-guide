# Lesson 2 · Debugging With AI & Knowing When to Reset Chat

> Classic beginner trap: the app crashes, you send a cropped screenshot or *"it still doesn't work, fix it"*, and the AI panics—editing 6 unrelated files until the working parts break too.

---

## 1. How to Feed Errors So the AI Fixes Them in One Shot

Copy-paste these **4 items** together:

```text
1. [Last Change]: Which file or command I just modified/ran.
2. [Trigger]: Exact button click or CLI command that reproduced the crash.
3. [Full Error Context]: Paste the last 30 lines of terminal stderr OR the full browser F12 Console error including file paths & line numbers (never just one line).
4. [Diagnose Before Editing]: Read the cited file and explain the root cause first—do not scatter speculative edits across multiple files.
```

---

## 2. The 2-Strike Circuit Breaker

When an LLM enters a **hallucination repair spiral**, each patch hides the last bug by breaking something else:

1. **Stop Trigger**: If **2 consecutive fix attempts on the same error yield no new diagnostic info**—or the AI starts modifying unrelated files—**stop immediately**. *(If attempt #2 genuinely narrowed the root cause with new evidence, keep going.)*
2. **Painless Rollback**: Run `git stash push -u -m "stop-loss"` (or `git revert HEAD` if committed) to return cleanly to your last working baseline.
3. **Re-anchor**: From clean state, ask the AI *why* the previous two attempts failed before trying a fresh path.

---

## 3. When to Ditch a Bloated Chat and Start Fresh

Long conversations packed with stack traces and failed code cause **Context Rot**—even frontier models lose track of constraints late in a session.

Open a **fresh chat** whenever:
- The thread exceeds ~15–20 turns or hits context compaction;
- The AI forgets your tech stack or repeats the exact same mistake;
- You just hit the **2-Strike Breaker** and rolled back via Git.

**3-Line Fresh-Session Handoff Template**:
```text
Starting a fresh session on this repo:
1. Workspace is clean at the latest baseline (`git status` / live files are ground truth).
2. Already working: [briefly list working features].
3. Next single goal: [one concrete task or bug]. Read the relevant files first before editing.
```
