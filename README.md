<div align="center">

<img src=".github/assets/cover.png" alt="True??? All Done! Boos! — AI Collaboration Survival Guide Cover" width="760" />

# 🛟 AI Collaboration Survival Guide · AI 协同生存指南

**"When your AI says 'All tests passed!', that is the exact moment to double-check."**  
**“AI 说‘全部通过’的时候，才是最该查的时候。”**

[![CI](https://github.com/reiwhale/ai-collaboration-survival-guide/actions/workflows/hook-tests.yml/badge.svg)](https://github.com/reiwhale/ai-collaboration-survival-guide/actions/workflows/hook-tests.yml)
[![Code & Templates: MIT](https://img.shields.io/badge/Code_%26_Templates-MIT-blue.svg)](LICENSE)
[![Handbook: CC BY-SA 4.0](https://img.shields.io/badge/Handbook-CC_BY--SA_4.0-lightgrey.svg)](LICENSE-DOCS)
![Lite Rules](https://img.shields.io/badge/Lite-2.0_KB_%2F_12_lines-blue)
![Hooks](https://img.shields.io/badge/Hooks-741_assertions_%7C_0_failures-brightgreen)
[![Research](https://img.shields.io/badge/Research-526K_2x2_Ablation_%28150_trials%29-purple)](research/README.md)

<h3>
  <a href="cn/README.md">🇨🇳 进入简体中文版（Chinese Edition）</a>
  &nbsp;&nbsp;·&nbsp;&nbsp;
  <a href="en/README.md">🇺🇸 Read in English（English Edition）</a>
  &nbsp;&nbsp;·&nbsp;&nbsp;
  <a href="research/README.md">🔬 研究报告与复现（Empirical Research）</a>
</h3>

</div>

---

A **~2.0 KB / 12-line zero-friction rule kit** + self-contained **Agent Skill** + **5 practical lessons** + **cross-platform PreToolUse speed-bump hooks** (zero-dependency Python lexer + POSIX `awk` / PowerShell fallbacks, verified by 741 automated assertions) for safe human-AI coding collaboration.

一套 **约 2.0 KB / 12 行零磨擦防翻车规则** + 独立自包含 **Agent Skill** + **五堂人机对齐实战课** + **跨平台终端防手滑钩子**（零依赖 Python 状态机核心 + POSIX `awk` / PowerShell 自动兜底，741 项自动化断言实测 0 失败）。

## Directory Overview · 目录总览

```text
.
├── cn/                 🇨🇳 完整自包含简体中文版 -> cn/README.md
│   ├── README.md         中文主指南、一键挂载/卸载提示词与宿主适配矩阵
│   ├── handbook/         人机协同实战五课（对齐 / 排错 / 后悔药 / 防糊弄 / 审计）
│   ├── templates/        AGENTS.lite.md（~2.0 KB）、Strict、LESSONS、MODEL_FIT
│   ├── skills/           中文自包含 Agent Skill（skills/ai-survival-guard/SKILL.md）
│   ├── guardrails/       Git 保命速查表 + 跨平台 Hook（py/ps1/sh）+ 样例 + 741 断言测试集
│   └── scripts/          宿主机环境只读探测脚本（probe_env.py）
│
├── en/                 🇺🇸 Self-contained English Edition -> en/README.md
│   ├── README.md         English main guide, one-click install/uninstall prompts & matrix
│   ├── handbook/         5 practical lessons (alignment, debugging, undo, fake-green, audit)
│   ├── templates/        AGENTS.lite.md (~2.0 KB), Strict, LESSONS, MODEL_FIT
│   ├── skills/           English self-contained Agent Skill (skills/ai-survival-guard/SKILL.md)
│   ├── guardrails/       Git undo cheatsheet + cross-platform hooks (py/ps1/sh) + examples + tests
│   └── scripts/          Read-only host environment probe (probe_env.py)
│
├── research/           🔬 526K 2×2 消融实证研究报告与 150 局复现包 -> research/README.md
│   ├── paper-2x2-526k.{zh,en}.md   中英双语完整实证论文（含 8 篇参考文献）
│   ├── scripts/        脱敏复现脚本（run_ablation_526k.py）与一键离线验真（verify_results.py）
│   └── data/           150 局全脱敏原始 JSONL 实验日志（~190 KB）
│
├── .github/            Contributing guide, cover artwork, mirror-sync check & 3-OS CI
├── LICENSE             MIT License (standard unmodified text)
└── LICENSE-DOCS        CC BY-SA 4.0 (handbook lessons, papers, artwork & guide prose)
```

## Dual License · 双协议全覆盖声明

Every file in this repository falls clearly under one of two licenses:

| Scope / 覆盖范围 | License / 协议 | Practical Meaning / 实用说明 |
|---|---|---|
| **Templates, Skills, Scripts, Guardrails, Benchmark Code/Data, CI & Repo Config**<br>`cn\|en/{templates,skills,guardrails,scripts}/`, `research/{scripts,data}/`, `.github/{scripts,workflows}/`, `.github/CONTRIBUTING.md`, `.gitignore`, `.gitattributes` | [**MIT License**](LICENSE) | Free to copy into any personal or commercial repo with zero copyleft friction; just keep attribution. / 零阻力直接抄进任何个人或商业项目，保留署名即可。 |
| **Handbook Lessons, Empirical Papers, Cover Artwork & Guide Prose**<br>`cn\|en/handbook/`, `research/README.md`, `research/paper-*.md`, `.github/assets/`, `README.md`, `cn/README.md`, `en/README.md` | [**CC BY-SA 4.0**](LICENSE-DOCS) | Commercial use & private edits welcome; publicly redistributing modified lessons/guides (including paid courses) **must credit authors and stay open under CC BY-SA 4.0**. / 允许商用与私下魔改；公开再分发修改版手册或卖课必须署名并以同协议开源，禁止洗稿闭源。 |

---

<sub>🥚 <b>Credits Easter Egg · 开发彩蛋</b> | Builders / 开发者: <code>Neon/Hydrogen Gemini (氖/氢基米) 🐱</code> &amp; <code>USER Rei (@reiwhale) 👻</code> | Canary Testers / 测试模型: <code>Opus5.5 High 📚(Strict)</code> · <code>DeepseekV4.1F 10/19 Max 🐋(Light Model)</code></sub>
