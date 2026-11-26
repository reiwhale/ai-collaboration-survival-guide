# Lesson 1 · Requirement Alignment & Breaking Tasks Down

> 80% of AI coding disasters are decided before the first line of code is generated.  
> **When you give a vague one-sentence wish, the model fills the remaining 90% with guesswork—and ends up building something you never wanted.**

---

## 1. Why One-Liner Prompts Backfire

- ❌ **Vague prompt**: *"Build me a clean to-do web app with export support."*
  - The AI invents the stack (React vs plain HTML), decides storage without asking, and dumps 800 lines of half-wired dependencies that crash on first run.
- ✅ **Aligned prompt**: **Goal + Constraints + Untouchable Boundaries + Plan First**.

---

## 2. Universal Requirement Alignment Template (Copy & Fill)

Before starting any non-trivial feature, send these 4 lines:

```text
[Goal]: One crisp sentence on what this change must achieve (e.g., add a CSV export button to the existing table).
[Input -> Output]: When the user clicks/inputs X, the exact expected output or UI result is Y.
[Constraints & Do-Not-Touch]: Stack/library limits, and files/modules that MUST NOT be modified.
[Plan First]: List the files you plan to edit and steps before writing code; wait for my "go" if architectural changes are involved.
```

> 💡 **Smoother Clarification Tip**: If the AI throws a wall of jargon and asks *"Which approach do you prefer?"*, reply: **"Give me 2–3 options with a recommended pick and a one-line plain explanation."** (GUI hosts pop up clickable cards with built-in free-text input; in plain terminals, you just reply with a single letter.)

---

## 3. The 3-Milestone Rule (Never Request 10 Features in One Prompt)

Split big ideas into **3 runnable, testable checkpoints**:

1. **Milestone 1 · Minimal Runnable Skeleton**: Render one clean page/endpoint (stub data is fine—prove dependencies and startup command run cleanly).
2. **Milestone 2 · Core Happy Path**: Wire real data logic and click through one complete end-to-end flow.
3. **Milestone 3 · Polish & Edge Cases**: Add export, modals, keyboard shortcuts, and error states last—**and run a Git commit after each milestone**.

---

## 4. Five Core Alignment Habits

1. **Questions stay read-only**: Asking *"should we / why / is it"* must yield analysis only—zero edits.
2. **Plans before irreversible actions**: Anything that cannot be undone in one Git step (deleting untracked files, wiping data, mutating external services, force-pushing) requires `Target Path | Intent | Blast Radius` first (see [`../templates/AGENTS.lite.md`](../templates/AGENTS.lite.md)).
3. **No unrequested "drive-by" refactors**: Formatting or refactoring unrelated code without your go-ahead is out of scope.
4. **Code > Stale Docs**: Treat untouched `README`s or comments as reference only; verify current symbol names directly in live source code.
5. **Surface uncertainty first**: Require unknowns and verification preconditions at the top of answers, never buried in footnotes.
