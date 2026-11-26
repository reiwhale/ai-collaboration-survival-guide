# Contributing · 贡献指南

Welcome! 欢迎提交 Issue 与 Pull Request，共同打磨这份面向初学者与工程团队的 AI 协同生存指南。

## 1. 提交 PR 前的 3 条硬要求 / Before Opening a PR

1. **双语同步（Bilingual Sync）**：修改 `cn/` 中文正文、模板或护栏文档时，请在同一 PR 中同步更新对应的 `en/` 英文镜像，保持结构与口径一致。
2. **改动 Hook 必跑回归并双端同步（Hook Changes Need Tests & Mirror Sync）**：修改 `cn/guardrails/hooks/block-dangerous.{py,ps1,sh}` 或 `examples/` 时，必须把同一改动同步到 `en/guardrails/hooks/` 下的镜像文件并补齐正反用例，在本地运行以下命令确认 **0 失败**：
   ```bash
   python en/guardrails/hooks/tests/run_hook_tests.py
   python cn/guardrails/hooks/tests/run_hook_tests.py
   python en/scripts/probe_env.py --dry-run
   ```
3. **不把 `AGENTS.lite.md` 养胖（Keep Lite Lean）**：`AGENTS.lite.md` 的核心价值是“零磨擦、不拖慢小模型”，请勿往 Lite 模板中追加长流程规范；进阶内容请放进 `cn/handbook/05-*`（或 `en/handbook/05-*`）或 `AGENTS.strict.md`。

## 2. 提交 Bug / 误伤报告请附环境矩阵 / Reporting Issues

请尽量附带：
- **OS & Shell**：例如 `Windows 11 + PowerShell 5.1` / `macOS 15 + zsh` / `Ubuntu 24.04 + bash`
- **宿主工具 & 模型**：例如 `Claude Code` / `Cursor` / `Antigravity` + 模型名称
- **复现命令与实际退出码**：例如 `bash block-dangerous.sh --test "..." ; echo $?`

## 3. 隐私与安全承诺 / Privacy Note

本仓库内所有脚本（`cn|en/guardrails/hooks/`、`cn|en/scripts/probe_env.py`）均为纯本地只读/拦截工具，**不联网、不回传任何遥测或代码内容、不读取 `.env` 与密钥**。
