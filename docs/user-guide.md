# neat-freak 用户手册

> 面向使用者的完整指南：安装、触发、两种工作模式、交付物解读与常见问题。
> 技术实现细节见 [技术手册](technical-manual.md)。

## 1. neat-freak 是什么

**neat-freak（洁癖）是一个跨平台 Agent Skill**，安装到 Claude Code / OpenAI Codex / OpenCode / OpenClaw / WorkBuddy 后，让 Agent 在会话中扮演"知识库编辑"角色：审查全局、合并重复、修正过期、删除废弃，让项目的文档和记忆始终与代码保持一致。

**一句话定位**：文档漂移的审计员——不存记忆、不做检索，只做一件事：让文档和记忆跟代码保持一致。

它与记忆持久化类 Skill（claude-mem、agentmemory 等）的区别：

| 维度 | 记忆持久化类 Skill | neat-freak |
|------|-------------------|------------|
| 核心动作 | 写入记忆（捕获→存储→检索注入） | 审查对齐（比对→修正→精简） |
| 时序 | 会话中捕获 | 会话后审查 |
| 产物 | 持久化记忆库 | 与代码一致的文档 + 精简记忆 |
| 依赖 | 需要存储/检索基础设施 | 零依赖，靠 Agent 自身能力 |
| 解决的问题 | "AI 失忆" | "记住的东西对不对" |

## 2. 安装

### 方式一：命令行安装（推荐）

```bash
git clone https://github.com/Asaceoo/neat-freak-skills.git /tmp/neat-freak
```

然后按你使用的平台复制 `skill/` 目录内容：

```bash
# Claude Code
cp -r /tmp/neat-freak/skill/* ~/.claude/skills/neat-freak/ && rm -rf /tmp/neat-freak

# OpenAI Codex
cp -r /tmp/neat-freak/skill/* ~/.codex/skills/neat-freak/ && rm -rf /tmp/neat-freak

# OpenClaw
cp -r /tmp/neat-freak/skill/* ~/.openclaw/skills/neat-freak/ && rm -rf /tmp/neat-freak

# OpenCode（自动扫描 Claude/Codex 目录，装一处即可）
cp -r /tmp/neat-freak/skill/* ~/.claude/skills/neat-freak/ && rm -rf /tmp/neat-freak

# WorkBuddy（用户级技能目录）
cp -r /tmp/neat-freak/skill/* ~/.workbuddy/skills/neat-freak/ && rm -rf /tmp/neat-freak
```

### 方式二：手动复制

把仓库 `skill/` 目录下的 `SKILL.md` 和 `references/` 复制到对应目录：

| Agent runtime | skills 目录 |
|---------------|-------------|
| Claude Code | `~/.claude/skills/neat-freak/` |
| OpenAI Codex | `~/.codex/skills/neat-freak/` |
| OpenClaw | `~/.openclaw/skills/neat-freak/` |
| OpenCode | `~/.claude/skills/neat-freak/`（自动扫描 Claude/Codex 目录，装一处即可）|
| WorkBuddy | `~/.workbuddy/skills/neat-freak/` |

安装完成后无需任何配置，重启会话即可被识别。

## 3. 怎么触发

neat-freak 按**语义**匹配你的意图，不要求精确字符串。有两种模式：

### 常规同步（对齐现有文档与代码）

把文档和记忆对齐到当前代码状态。触发语：

- "同步一下" / "sync up" / "整理一下" / "tidy up"
- "/sync" / "/neat"
- "搞一下文档" / "搞一下" / "收尾" / "这个阶段做完了"

### 初始化（从零建立项目知识体系）

适合接手新项目、或项目文档严重缺失时。触发语：

- "初始化项目" / "初始化下项目" / "初始化一下"
- "首次梳理" / "从头整理" / "init project" / "bootstrap docs"

> **判断规则**：你的显式意图优先。说"初始化"就走初始化，说"同步"就走常规同步——即使项目缺文档也不会自动切换模式。你没表态时，Agent 会根据项目现状（有无 CLAUDE.md / README / docs/）自动判断。

## 4. 两种模式的使用体验

### 4.1 常规同步：说完"同步一下"会发生什么

1. **尺寸体检**：先检查 CLAUDE.md / MEMORY.md 是否超尺寸（超限的部分会被静默截断，等于没记），膨胀优先处理。
2. **盘点现状**：枚举项目的 docs/、README、CLAUDE.md / AGENTS.md、记忆文件、配置文件、CI/CD 配置。
3. **识别变更影响**：把本次会话的新事实（新增 API、环境变量、数据表等）映射到所有应更新的文档。
4. **实际修改**：用工具真正改文件，不是只给建议。
5. **自检清单**：14 项检查逐项核对（尺寸、漏改、链接有效性、相对时间清零等）。
6. **变更摘要**：按项目分组列出所有改动文件。

你只需最后看一遍变更摘要；记忆之间出现无法自动判断的矛盾时会暂停问你，其余情况自动拍板。

### 4.2 初始化：说完"初始化项目"会发生什么

1. **代码事实提取**：从代码中提取项目类型、技术栈、命令、环境变量、API 端点、数据模型等事实清单。
2. **一致性审查**：逐条比对文档与代码事实，输出审查报告（每个问题标注 🔴 高 / 🟡 中严重度）。
3. **停下来等你确认**：输出操作清单（修复不一致 → 补缺失 → 优化），**未经你确认不会动任何文件**。
4. **执行**：你确认全部 / 部分 / 调整后，按清单执行。
5. **终检**：一致性逐条终检 + 写入初始化标记 + 变更摘要。

确认方式：回复"全部确认"、"只执行第 1、3 项"、或直接说要调整哪里。

## 5. 交付物怎么读

| 交付物 | 出现场景 | 关注点 |
|--------|----------|--------|
| **审查报告** | 初始化 | "一致性问题表"里的 🔴 项危害最大（错误信息比缺失信息危害更大） |
| **操作清单** | 初始化 | 按 🔴 修复不一致 / 🟡 新建文件 / 修改文件 / 迁移文件 分组，逐项勾选确认 |
| **变更摘要** | 所有模式 | 按"记忆变更 / 文档变更 / 配置与 CI/CD 变更 / 未处理"分组；**"未处理"是唯一需要你跟进的** |

初始化完成后，项目根的 CLAUDE.md（或 AGENTS.md）末尾会出现 `<!-- neat-freak: initialized at <日期> -->` 标记，用于后续模式判断。

## 6. 安全边界（它不会做什么）

- **只修改文档和记忆文件，不碰代码**。审查中发现疑似代码 bug 时，文档保持描述"正确行为"，bug 列入"未处理"提醒你修代码。
- **初始化必须用户确认**后才执行操作清单。
- **常规同步自动执行**，但记忆矛盾时暂停问用户。
- **删除记忆文件前列出清单**，不静默删除。
- **全局配置极度克制**——只有你明确表达跨项目核心原则时才动 `~/.claude/CLAUDE.md` 等全局文件。

## 7. 常见问题

**Q：说了触发词但没反应？**
确认 SKILL.md 已复制到对应平台的 skills 目录（见 §2 路径表），且重启了会话。触发按语义匹配，描述意图即可（如"把文档和代码对一下"），不必背触发词。

**Q：我的项目没有 docs/ 目录，直接说"同步"行不行？**
行。常规同步会按现状对齐，不会擅自初始化。想要完整文档体系时再明确说"初始化项目"。

**Q：记忆文件已经膨胀到上百个怎么办？**
直接说"整理一下"。neat-freak 的"毕业"机制会把重复出现 3 次以上的稳定教训、本属"系统怎么工作"的知识迁入 docs/，原记忆缩成一行指针或删除。

**Q：我同时用 Claude Code 和 Codex 怎么办？**
CLAUDE.md 和 AGENTS.md 功能等价，只维护一份主文件，另一份用一行 `See CLAUDE.md` 跳转。docs/ 和 README 是平台中立的，不用分两份。

**Q：初始化报告里有我不想改的项？**
在确认阶段说明即可，只执行你确认的部分，其余列入"未处理"。

**Q：它会不会把我的代码改坏？**
不会。neat-freak 全程不修改代码文件；文档向代码对齐是它的基准方向，反向修改（把文档改成与代码 bug 一致）被明确禁止。

## 8. 验证安装

仓库根目录的 `test-prompts.json` 提供 3 个典型测试场景（初始化新项目 / 功能开发后同步 / 口语化触发），每个场景含 `expected_behavior`、`verification_points` 和 `expected_output`（`must_contain` / `must_not_contain`），可在新会话中逐条验证技能行为是否符合预期。

## 9. 文档索引

| 文档 | 内容 | 读者 |
|------|------|------|
| [README](../README.md) | 项目概览、快速开始、示例 | 所有人 |
| [用户手册](user-guide.md)（本文） | 安装、触发、使用流程、FAQ | 使用者 |
| [技术手册](technical-manual.md) | 架构、流程机制、扩展指南 | 开发者 / 贡献者 |
| [CHANGELOG](../CHANGELOG.md) | 版本历史 | 所有人 |
