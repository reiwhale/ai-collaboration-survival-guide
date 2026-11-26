# PreToolUse 防手滑减速带安装指南

> 纯靠 Markdown 文字提醒“禁止 `rm -rf *`”，模型在上下文压缩后仍可能忘掉。  
> 下方配置利用 **PreToolUse（工具执行前钩子）** 在命令真正落地前做一次状态机词法筛查，命中即返回 **`exit 2`（Claude Code 约定的硬拦退出码）** 阻断该次调用。
>
> ⚠️ **先讲真话（定位边界）**：终端钩子只是**“防手滑减速带”**，不是绝对安全沙箱。它采用跨平台零依赖状态机引擎 [`block-dangerous.py`](block-dangerous.py)（准确识别嵌套引号、注释、Heredoc、多行提交、管道与常见变体），但仍拦不住指定目录名强删或脚本内联删除（见第四节）。**真正的底层兜底永远是 Git 本地存档 + 宿主终端审批开关**。

---

## 一、如何接入 Claude Code（项目级 `.claude/settings.json`）

> **宿主适配说明**：下方配置文件格式目前**仅针对 Claude Code**。如果你使用 **Cursor / Codex CLI / Gemini CLI / Antigravity** 等其他工具，请优先使用本仓库的 [`AGENTS.lite.md`](../../templates/AGENTS.lite.md) + **Git 存档** + 宿主自带的命令审批确认框。

### 第 1 步：复制钩子文件到你的项目 `.claude/hooks/`
- **推荐（全平台最稳、毫秒级）**：复制 [`block-dangerous.py`](block-dangerous.py) 到 `.claude/hooks/`（如使用 `.sh` / `.ps1` 薄壳入口，将同目录的 `.py` 与对应 `.sh` 或 `.ps1` 一并放入 `.claude/hooks/`，壳脚本会自动优先调用同级 `.py`；若机器无 Python 则自动降级到纯 Shell/POSIX `awk` 兜底）。

### 第 2 步：在 `.claude/settings.json` 添加钩子配置（三选一，[`examples/`](examples/) 提供现成文件）

#### 方案 A · 跨平台通用（推荐 · 适用于 Windows 全部 Shell / macOS / Linux）
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python -B .claude/hooks/block-dangerous.py"
          }
        ]
      }
    ]
  }
}
```
> 现成样例：[`examples/claude-settings.windows.json`](examples/claude-settings.windows.json)。使用正斜杠相对路径，在 Windows 的 **cmd.exe / PowerShell 5.1 / Git Bash** 三种底座下均可直接运行，彻底避开 `%CLAUDE_PROJECT_DIR%` 在 Git Bash 下不展开导致静默 fail-open 的历史大坑。（macOS / Linux 若仅装 `python3` 可把 `python` 改为 `python3`，或使用下方方案 B。）

#### 方案 B · macOS / Linux / Git Bash（支持无 Python 自动降级）
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/block-dangerous.sh\""
          }
        ]
      }
    ]
  }
}
```
> 现成样例：[`examples/claude-settings.unix.json`](examples/claude-settings.unix.json)。记得先赋权：`chmod +x .claude/hooks/block-dangerous.sh`。

#### 方案 C · Windows PowerShell 薄壳入口（解决默认 `Restricted` 策略阻断 `.ps1`）
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "powershell -NoProfile -ExecutionPolicy Bypass -File .claude/hooks/block-dangerous.ps1"
          }
        ]
      }
    ]
  }
}
```
> 现成样例：[`examples/claude-settings.windows-powershell.json`](examples/claude-settings.windows-powershell.json)。若你的项目会在非根目录子路径触发钩子，可把相对路径替换为项目绝对路径（正斜杠 `/` 在 Windows PowerShell / Git Bash / cmd 中普遍兼容）。

---

## 二、两步必跑验收（防“装了其实没生效”）

> ⚠️ **重要风控（Fail-Open 风险）**：在 Claude Code 的钩子协议中，只有返回 **`exit 2`** 才会硬阻断；如果脚本路径写错、缺权限、或内部异常返回了 `exit 1` / `127` 等**非 0 非 2 退出码，宿主默认会放行（fail-open）**！装完必须走完下面两步：

### 第 1 步：脚本本地自检
- **跨平台 Python 核心引擎**：
  ```bash
  python -B .claude/hooks/block-dangerous.py --test "rm -rf *.py"
  ```
- **Windows PowerShell**：
  ```powershell
  powershell -NoProfile -ExecutionPolicy Bypass -File .claude/hooks/block-dangerous.ps1 -TestCommand "rm -rf *.py"
  echo "EXIT=$LASTEXITCODE"   # 期望输出 BLOCKED BY GUARDRAIL 且 EXIT=2
  ```
- **Bash / Git Bash**：
  ```bash
  bash .claude/hooks/block-dangerous.sh --test "rm -rf *.py" ; echo "EXIT=$?"
  # 期望输出 BLOCKED BY GUARDRAIL 且 EXIT=2
  ```
- 在本仓库根目录可一键跑完整可复现测试集（含红队绕过、高频防误拦、64KB 大载荷防死锁、畸形 JSON 与无 Python 纯壳兜底回归）：
  ```bash
  python cn/guardrails/hooks/tests/run_hook_tests.py
  python en/guardrails/hooks/tests/run_hook_tests.py
  ```

### 第 2 步：在 Claude Code 里做真实接线验收（关键！）
重启或重新加载 Claude Code 会话，发一句无害探针指令让它通过 Bash 工具执行一条不存在通配符的测试命令：
```text
请用 Bash 工具执行：rm -rf *.probe_nonexistent_999
```
- ✅ **看到工具被拦截并打印 `BLOCKED BY GUARDRAIL`** → 接线真正生效。
- ❌ **直接静默执行完毕（即使没删掉东西）** → 说明 `.claude/settings.json` 路径或权限有误，钩子正处于 fail-open 失效状态，务必排查后再开工！

---

## 三、实测环境矩阵与跨平台说明

| 环境 | 入口脚本 | 引擎与兜底 | 新手注意 |
|---|---|---|---|
| **Windows 11 + PowerShell 5.1 / cmd / Git Bash** | [`block-dangerous.py`](block-dangerous.py) / [`block-dangerous.ps1`](block-dangerous.ps1) / [`block-dangerous.sh`](block-dangerous.sh) | 优先零依赖 `.py` 状态机；无 Python 时自动降级纯 PS1 / POSIX `awk` | `.ps1` 必须带 `-NoProfile -ExecutionPolicy Bypass`；推荐直接配方案 A（`.py`）避开 Shell 差异 |
| **macOS / Linux** | [`block-dangerous.py`](block-dangerous.py) / [`block-dangerous.sh`](block-dangerous.sh) | 优先 `python3` 运行 `.py`；无 Python 时走 POSIX `awk`（兼容 macOS BSD 工具链，不使用 GNU `sed` `\n`） | 作者无本地 Mac/Linux 真机，由 GitHub Actions `macos-latest` / `ubuntu-latest` CI 自动验证；启用前请务必完成本地两步验收 |

---

## 四、覆盖范围与诚实绕过边界（必读）

- **本减速带能拦住什么**：
  - 通配符删除（含 PowerShell 引号通配符与管道）：`rm *.py`、`rm -rf "*.py"`、`Remove-Item "*.py"`、`Get-ChildItem *.py | % { Remove-Item $_ }`、`find ... -delete / -execdir rm`、`xargs /bin/rm`、`cmd /c del /f /s /q *.py`；
  - 根 / 盘符 / 家 / 当前 / 上级目录递归强删：`rm -rf /`、`~/`、`$HOME`、`.`、`./`、`../`、`Remove-Item -Rec -Fo .`、`ri -r -fo .`、`$env:USERPROFILE`、`rd /s /q C:\`；
  - 破坏性 Git（支持 `-C` / `--no-pager` 等全局参数与乱序参数）：`git reset --hard`、`git clean -f`（放行 `-n/--dry-run`）、`git push -f / --force / -fu / --mirror`（放行 `--force-with-lease`）、`git checkout/restore .` 与 `./`、`git stash clear/drop`、`git branch -D`；
  - 破坏性 DB / IaC / 磁盘命令：`DROP TABLE/DATABASE/SCHEMA`、`TRUNCATE [TABLE]`、`terraform destroy` / `apply -destroy`、`mkfs.*`、`dd of=/dev/...`、`chmod -R /`；
  - 常见绕过加固：识别 `bash -c` / `powershell -c` / `cmd /c` / `eval` / `$(...)` / `(rm -rf /)` / `sudo -u root` / `r\m` 等壳内与包装器写法，且防单双引号词法错配与 64KB 管道死锁。
  - **严格防误伤**：状态机原生识别跨行引号、Heredoc、行尾 `#` 注释与逐段命令类型，`cd app && git commit -m "fix DROP TABLE"`、`cat << 'EOF' ...`、`python -c "assert 'DROP TABLE'..."`、`pytest -k "DROP TABLE"`、`ls | xargs grep -n rm`、`rm old.log # delete?`、`Remove-Item -Recurse -Force .\node_modules` 均正常放行。
- **它明确拦不住什么（公开绕过边界）**：
  - **指定目录名强删**：例如 `rm -rf src`、`Remove-Item -Recurse -Force src`、`cmd /c rd /s /q src`（无法安全区分 `node_modules` 与业务目录，刻意不盲拦）；
  - **通用脚本语言内联删除**：例如 `python -c "import os..."`、`node -e "fs.rmSync(...)"`；
  - **Git refspec 强推语法**：例如 `git push origin +main`；
  - **非终端工具通道**：IDE 自带的原生文件删除 API 不经过 Bash 钩子。
- **结论很简单**：把 Hook 当作第一道**防手滑减速带**，永远不要因为它装好了就关掉 Git 本地存档或宿主的高危审批弹窗！
