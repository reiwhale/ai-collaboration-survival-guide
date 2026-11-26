# Project Lessons Ledger (Cold Layer · On-Demand Lookup Only)

> **Purpose**: Store project-specific traps and local conventions here instead of bloating root `AGENTS.md`.  
> **Rule**: Do not load this entire file every turn. Inspect or append here only when debugging matching modules or performing hot-layer eviction.

---

## Evolution Lifecycle (Hot / Cold Metabolism)

1. **New bugs go Cold first**: Append newly discovered project pitfalls below—**never tack ad-hoc patches onto `AGENTS.md`**.
2. **Promote on recurrence**: Only when a pitfall repeats **>= 2 times** across different tasks and affects the whole repo should you distill 1 concise line into `AGENTS.md`.
3. **90% Hot-Layer Eviction**: When your hot `AGENTS.md` hits **90% of its cap** (`Lite` cap ~30 lines / 2.5 KB -> 90% ~27 lines / 2.2 KB; `Strict` cap 80 lines / 5.5 KB -> 90% ~72 lines / 5 KB), you **must move one low-frequency, outdated, or module-specific rule back here** (or into a module README) before adding anything new.

---

## Append-Only Pitfall Log

| Date | Module / Context | What Broke | Actionable Countermeasure (+ Check) | Eviction / Expiry Condition |
|---|---|---|---|---|
| `YYYY-MM-DD` | `example: db-migrate` | `Migration wiped local dev seed data` | `Print DB host & require explicit dev flag before running seed reset` | `Evict once isolated test containers are enforced in CI` |
