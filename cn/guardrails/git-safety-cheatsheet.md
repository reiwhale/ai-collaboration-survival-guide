# Git 保命速查表（跨平台 · 零基础后悔药）

> 永远不要指望用聊天记录里的 `Ctrl+Z` 撤回 AI 的批量修改。  
> 全部命令已拆成**逐行写法**，不使用 `&&`，在 Windows PowerShell 5.1 与 macOS/Linux Bash 下均可直接执行。

---

## 先分清三个容易混淆的目录/概念

1. **Git 暂存区（Index）**：运行 `git add` 后等待提交的那批改动（Git 内部概念）。
2. **`git stash`（临时救命抽屉）**：把**还没提交**、但已经改乱的改动一键打包收起，让文件立刻退回干净状态。
3. **`_trash_box/`（待清空回收盒）**：放在项目里的本地垃圾文件夹（已被 `.gitignore` 屏蔽）。AI 想清理废稿时先放这里，等你跑稳项目后随时删掉这一个文件夹。

---

## 0. 开工前必查：我的项目有“存档槽”吗？

在项目文件夹打开终端，运行：
```text
git status
```
如果提示 `not a git repository`，说明处于**裸奔状态**。先初始化仓库（若本机首次使用 Git 尚未配过身份，紧接着设下面两行本地签名，否则 `commit` 会报错）：
```text
git init
git config user.name "Your Name"
git config user.email "you@example.com"
git add .
git commit -m "chore: initial baseline"
```

---

## 1. 最重要的 3 组保命命令

### ① 让 AI 大改前：先存一个存档点
```text
git add -A
git commit -m "checkpoint: before AI edit"
```

### ② AI 改完以后：先看动了哪些文件
```text
git status -s
git diff --stat
```
想逐行核对改了什么：
```text
git diff
```

### ③ 发现 AI 把项目改崩了：按场景退回

- **情况 A（还没 `git commit`，刚刚改坏）—— 收进救命抽屉**：
  ```text
  git stash push -u -m "broken-ai-attempt"
  ```
  > 以后想从抽屉里查看或取回代码：
  > ```text
  > git stash list          # 查看抽屉列表（如 stash@{0}）
  > git stash apply         # 取回最近一次改动，但保留抽屉里的备份（最稳妥）
  > git stash pop           # 取回最近一次改动，并清空这条抽屉记录
  > ```
  > **切忌乱敲 `git reset --hard`**，它会直接擦除未提交改动且进不了抽屉。

- **情况 B（刚刚已经 `git commit` 进去了，后来才发现有 Bug）—— 安全生成撤销提交**：
  ```text
  git revert HEAD --no-edit
  ```
  > `git revert` 会新增一笔“把上一次改动倒扣回去”的提交，**不抹掉历史**，最安全、最适合新手。

---

## 2. 进阶防线：用分支隔离 + 2 次熔断 + 回收盒

- **分支隔离高风险实验**：大重构前先切新分支 `git switch -c feat/ai-experiment`。成功再合回主线；改废了直接切回 `main` 丢弃实验分支。
- **2 次无新进展熔断**：AI 修同一个报错连续 **2 次尝试都没有新信息或新进展**，立刻喊停并用 `git stash push -u -m "stop-loss"` 回退基线，禁止越补越烂。
- **`_trash_box/` 待清空回收盒**：废旧代码/脚本先移入 `_trash_box/`；新版本跑稳两天后，用户手动确认一键删空 `_trash_box/` 即可。
