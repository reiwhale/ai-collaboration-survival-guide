# Model Sizing & Cross-Model Failure Playbook (`MODEL_FIT`)

> Why can't a single 30 KB constitution govern every LLM?  
> Because as instruction density and context length climb, **lightweight or heavily reasoning-routed models suffer non-linear "system prompt paralysis" and silent constraint drops**.

---

## 1. Quick Selection Matrix

| Model Tier / Examples | Recommended Template | Suggested Rule Cap | Key Safeguard |
|---|---|---|---|
| **Lightweight / Fast / Cost-Optimized**<br>e.g., `DeepSeek-V4.1-Flash`, `Gemini Flash`, `Claude Haiku`, `GPT-mini` | `AGENTS.lite.md` (`~2.0 KB` / 12 lines) | `<= 15` core rules, mostly affirmative phrasing | **Never inject heavy formatting specs or long style guides**; offload validation to external scripts instead of expecting detailed self-audits. |
| **Frontier / Deep Reasoning**<br>e.g., `Claude Opus / Sonnet`, `Gemini Pro`, flagship `GPT` | `AGENTS.lite.md` (daily)<br>`AGENTS.strict.md` (audits/refactors) | Keep root `AGENTS.md` `<= 80` lines; look up `handbook/` on demand | Still avoid repeating file trees or obvious stack trivia—prevent ETH's "over-obedience exploration" tax. |

---

## 2. Universal Agent Failure Symptoms -> Engineering Countermeasures

Regardless of provider, when long coding sessions go sideways, match the symptom below:

| Symptom (Observed Behavior) | Common Trigger | Universal Countermeasure |
|---|---|---|
| **1. "Announces Work, Does Nothing"**<br>Prints *"I will now inspect and edit file X..."* then stops with zero disk edits | Deep context (`>= 80K tokens`) + max reasoning effort | Split into short chats; verify real disk diffs with `git status` instead of trusting verbal promises; dial down reasoning effort if it repeats. |
| **2. "Thinking Budget Exhausted / Blank Answer"**<br>Internal chain-of-thought consumes output cap, leaving truncated or empty text | Open-ended *"research everything and output full results in one shot"* prompts | Break work into bounded single-step deliverables and validate outputs with external scripts. |
| **3. "Raw Tool Markup Leaks into Chat"**<br>Internal tool tags or malformed JSON print as plain text without running tools | Oversized tool schemas, noisy context, or format drift | Start a clean short session and trim unneeded tools for that step. |
| **4. "Hallucinated Context-Window Panic"**<br>Refuses to proceed claiming *"context almost full"* right after compaction | Models rarely see actual billing telemetry and misread long logs | Check the host/CLI's real token counter, while still rotating to a fresh chat before **120K–160K tokens** to avoid quality decay. |
| **5. "Mid-Session Rule Drift (Context Rot)"**<br>Earlier rules silently vanish mid-thread; scolding *"re-read rule #3"* fails | >15–20 turns packed with stack traces and failed edits | **Move Constraints Near + Externalize State**: paste the 1–2 rules needed right now at the **end of your current prompt**, and keep task state in a small disk checklist. |

---

## 3. Empirical Case Study: `DeepSeek-V4.1-Flash` + `reasoningEffort: max`

The table above was distilled from extended coding sessions on `DeepSeek-V4.1-Flash` with `reasoningEffort: max`, where five recurring black-box signatures (`M1–M5`) appeared:
- **Routing & Role**: Some API gateways alias names (e.g., `deepseek-v4-pro`) directly to `V4.1-Flash`. It shines as an **execution worker for well-scoped scripts, cleanup, and test runs**, not as a long-horizon monolithic architect.
- **Signatures**: `M1` (`finish_reason=stop` with empty `tool_calls` after announcing edits), `M2` (`reasoning_content` hitting `finish_reason=length`), `M3` (empty `content` on `stop`), `M4` (false context-full panic), and `M5` (raw `<｜DSML｜>` markup leaking into chat text).

---

## 4. Three-Line Cheat Sheet for Beginners

> **Split big jobs into short chats; give lighter models Lite rules only.**  
> **When thinking stalls, inspect files on disk—never trust verbal promises.**  
> **Leave catastrophic blocks to Git and host approvals, never to model willpower.**
