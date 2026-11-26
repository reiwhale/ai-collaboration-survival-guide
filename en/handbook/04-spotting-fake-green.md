# Lesson 4 · Spotting "Fake Green" & Knowing Model Quirks

> **"When your AI says 'All tests passed!', that is the exact moment to double-check."**  
> LLMs are trained to sound helpful and conclusive—which frequently leads them to present guesses as proof or pass mock-only unit tests while the real UI stays broken.

---

## 1. Four Classic AI Excuses & What to Ask Back

| What the AI Says | Common Reality Behind It | What You Ask Immediately |
|---|---|---|
| *"All tests passed! Everything works."* | It mocked the database/API, or tested 3 shallow cases while the real page crashes | **"Show the exact test command + stdout, and list what real user flows are NOT tested."** |
| *"I have fixed the bug."* | Didn't re-read disk, fixed an unrelated flag, or hit M1 (empty tool calls) | **"Run `git diff` to show what actually changed, plus live command output."** |
| *"I searched everywhere—X doesn't exist."* | Search tool capped at 200 items, encoding failed, or wrong folder fence | **"Which exact folder did you scan? Prove the search works on a known existing file."** |
| *"This is probably caused by..."* | Guessed from function names without reading the actual file | **"Stop guessing. Read the source file and quote the exact line numbers."** |

---

## 2. Five Evidence Levels (Weakest-Link Rule)

1. **`[Observed]` (Hard Currency)**: Actual command stdout or file readback observed in this turn.
2. **`[Declared]` (Verify Before Trusting)**: Claims inside configs/docs (e.g., `model: pro` in YAML does not guarantee backend routing wasn't aliased).
3. **`[Inferred]`**: Logical deduction not yet tested at runtime.
4. **`[Self-Reported]`**: AI recalling *"I didn't touch that"*—always cross-check `git status` or mtime.
5. **`[Reference]`**: External blogs or stale docs; treat as unverified until reproduced locally.

---

## 3. Respect Model Sizing & Prevent Rule Bloat

- **Lightweight / Fast / Reasoning-Budget Tiers** (`DeepSeek-V4.1-Flash`, `Flash`, `Mini`, `Haiku`):
  - Never overload them with 30 KB rulebooks or strict multi-section formatting—stick to lean [`AGENTS.lite.md`](../templates/AGENTS.lite.md).
  - For cross-model failure symptoms (*announces work with zero edits, exhausted thinking budget, raw tool tag leaks, false context-full panic, mid-session rule drift*) plus the `DeepSeek-V4.1-Flash` case study, see [`../templates/MODEL_FIT.md`](../templates/MODEL_FIT.md).
- **Hot / Cold Evolution**: Keep new repo-specific traps in cold [`../templates/LESSONS.template.md`](../templates/LESSONS.template.md) (`docs/lessons.md`); promote only recurring `>= 2`-hit rules, and evict one stale rule whenever hot `AGENTS.md` hits ~90%.

---

## 4. Graduation Path: When to Trim or Drop These Rules

`AGENTS.lite.md` is a set of **training wheels**, not permanent handcuffs. Once your workflow matures, trim each rule when its condition holds:

| `AGENTS.lite.md` Rule | What Failure It Prevents | When Experienced Devs Can Drop It |
|---|---|---|
| **Rule 1 (Questions vs Irreversible Edits)** | Exploratory questions mutating files; wiping untracked files or live DBs | Your host enforces read-only Q&A mode + approval gates, and all DBs are isolated dev/test instances |
| **Rule 2 (Git Checkpoints + 2-Strike Breaker)** | Unrecoverable broken states and infinite blind-patch loops | You naturally work on feature branches with frequent commits and spot fix loops instantly yourself |
| **Rule 3 (Verified Facts + 3-Line Summary)** | Trusting mock-only green lights or hallucinated APIs | Your repo has real **CI integration / E2E tests** that serve as the automated source of truth |
| **Rule 4 (Live Code > Docs + Cold Ledger)** | Acting on stale READMEs and bloating `AGENTS.md` into paralysis | Your team keeps docs in sync and actively budgets prompt size |
