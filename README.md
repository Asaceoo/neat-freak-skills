# neat-freak

> **文档漂移的审计员** — 不存记忆、不做检索，只做一件事：
> 让文档和记忆跟代码保持一致。

[![Agent Skills](https://img.shields.io/badge/Agent-Skills-blue)]()
[![Claude Code](https://img.shields.io/badge/Claude-Code-green)]()
[![Codex](https://img.shields.io/badge/OpenAI-Codex-black)]()
[![OpenCode](https://img.shields.io/badge/Open-Code-orange)]()
[![OpenClaw](https://img.shields.io/badge/Open-Claw-red)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**为什么不是又一个记忆类 Skill？** claude-mem / agentmemory / ultra-memory 都在解决"怎么记住"，neat-freak 解决"记住的东西对不对"。三层知识分层（agent 记忆 / CLAUDE.md / docs）+ 毕业机制 + 14 项自检清单，让知识体系的每一层都跟得上代码的变化。

## 你什么时候需要它？

- **开发完一个功能**，不确定文档有没有跟上——说"同步一下"
- **接手一个项目**，发现 CLAUDE.md / AGENTS.md 和代码对不上——说"初始化项目"
- **记忆文件膨胀**到上百个，不知道哪些该留——说"整理一下"
- **阶段做完了**，要确保下一个 Agent 拿到的是准确的知识——说"收尾"
- **新人要直接上手**，需要文档跟代码完全一致——说"梳理一下"

## 它会交付什么？

| 场景 | 交付物 |
|------|--------|
| 初始化 | 一份审查报告（标注不一致/缺失项）+ 操作清单（等确认后执行）+ 变更摘要 |
| 常规同步 | 变更摘要（按项目分组列出所有改动文件）|
| 记忆清理 | 毕业后的精简记忆 + 迁移到 docs/ 的稳定知识 |

## 快速开始

### 安装

**方式一：命令行安装（推荐）**

```bash
# Claude Code
git clone https://github.com/Asaceoo/neat-freak-skills.git /tmp/neat-freak && cp -r /tmp/neat-freak/skill/* ~/.claude/skills/neat-freak/ && rm -rf /tmp/neat-freak

# OpenAI Codex
git clone https://github.com/Asaceoo/neat-freak-skills.git /tmp/neat-freak && cp -r /tmp/neat-freak/skill/* ~/.codex/skills/neat-freak/ && rm -rf /tmp/neat-freak

# OpenClaw
git clone https://github.com/Asaceoo/neat-freak-skills.git /tmp/neat-freak && cp -r /tmp/neat-freak/skill/* ~/.openclaw/skills/neat-freak/ && rm -rf /tmp/neat-freak

# OpenCode（自动扫描 Claude/Codex 目录，装一处即可）
git clone https://github.com/Asaceoo/neat-freak-skills.git /tmp/neat-freak && cp -r /tmp/neat-freak/skill/* ~/.claude/skills/neat-freak/ && rm -rf /tmp/neat-freak

# WorkBuddy
git clone https://github.com/Asaceoo/neat-freak-skills.git /tmp/neat-freak && cp -r /tmp/neat-freak/skill/* ~/.workbuddy/skills/neat-freak/ && rm -rf /tmp/neat-freak
```

**方式二：手动复制**

将 `skill/` 目录下的内容（`SKILL.md` 和 `references/`）复制到你的 Agent skills 目录：

| Agent runtime | skills 目录 |
|---------------|-------------|
| Claude Code | `~/.claude/skills/neat-freak/` |
| OpenAI Codex | `~/.codex/skills/neat-freak/` |
| OpenClaw | `~/.openclaw/skills/neat-freak/` |
| OpenCode | `~/.claude/skills/neat-freak/`（自动扫描 Claude/Codex 目录，装一处即可）|
| WorkBuddy | `~/.workbuddy/skills/neat-freak/` |

### 触发

在对话结束时说：

```
同步一下
```

或用斜杠命令：

```
/neat
```

**支持的 Agent runtime**：Claude Code · OpenAI Codex · OpenCode · OpenClaw

## 触发方式

**常规同步**（对齐现有文档与代码）：
- "同步一下" / "sync up" / "整理一下" / "tidy up" / "/sync" / "/neat"
- "搞一下文档" / "搞一下" / "收尾" / "这个阶段做完了"

**初始化模式**（从零建立知识体系）：
- "初始化项目" / "初始化下项目" / "初始化一下"
- "首次梳理" / "从头整理" / "init project" / "bootstrap docs" / "start fresh"

> 按语义匹配，不按精确字符串匹配。中文口语变体（"初始化下"、"搞一下"）和英文变体都能触发。

## 示例

### 示例 1：初始化新项目

**输入**：`初始化下项目`（项目无 CLAUDE.md、无 docs/、有 README.md 和 package.json）

**执行过程**：Step 0-init 提取代码事实 → Step 1-init 输出审查报告 → Step 2-init 输出操作清单等确认

**输出片段**（审查报告）：

```
## 初始化审查报告

### 项目概况
- 项目类型：Web 服务
- 技术栈：Node.js 20 + Express 4 + PostgreSQL 15
- 代码事实提取：12 个 API 端点、8 个环境变量、6 个顶层目录

### 一致性问题（核心）

| # | 文件 | 问题类型 | 文档描述 | 代码事实 | 严重度 |
|---|------|----------|----------|----------|--------|
| 1 | README.md | 命令过时 | `npm start` | 实际命令是 `npm run dev` | 🔴 高 |
| 2 | README.md | 环境变量遗漏 | 列出 3 个 | 代码中实际使用 8 个 | 🔴 高 |
| 3 | docs/api-reference.md | API 遗漏 | 列出 5 个端点 | 代码中注册了 12 个 | 🔴 高 |

### 待执行操作清单

### 🔴 修复不一致（优先）
- [ ] README.md — 修正启动命令 npm start → npm run dev
- [ ] README.md — 补充遗漏的 5 个环境变量
- [ ] docs/api-reference.md — 补充遗漏的 7 个 API 端点

### 🟡 新建文件
- [ ] CLAUDE.md / AGENTS.md — 从零创建，包含 11 个板块
- [ ] docs/architecture.md — 架构说明
- [ ] docs/getting-started.md — 本地开发指南

请确认以上操作，或告诉我需要调整的地方。
```

### 示例 2：功能开发后同步

**输入**：`同步一下`（本次会话新增了 2 个 API 端点和 1 个环境变量）

**执行过程**：第零步体检 → 第一步盘点 → 第二步识别变更影响 → 第三步实际修改 → 第四步自检 → 第五步变更摘要

**输出片段**（变更摘要）：

```
## 同步完成

### 文档变更（按项目分组）
- my-project/CLAUDE.md — 新增 JWT_SECRET 到环境变量表
- my-project/docs/api-reference.md — 新增 GET /api/users、POST /api/users 接口说明
- my-project/docs/architecture.md — Routes 小节新增 2 个端点
- my-project/docs/getting-started.md — 本地环境变量配置补充 JWT_SECRET

### 自检清单
✅ CLAUDE.md 净涨幅 ≤ 30 行（实际 +3 行）
✅ 新增 API 路由在 api-reference 和 architecture 都出现了
✅ 新增环境变量在 getting-started 和 CLAUDE.md 都出现了
✅ 没有相对时间遗留
✅ 文档内链接全部有效
```

### 示例 3：记忆毕业（防止膨胀）

**输入**：`整理一下`（MEMORY.md 已达 80 行松散记忆）

**执行过程**：识别可毕业的记忆 → 将稳定知识迁入 docs → 原记忆缩成指针

**输出片段**（毕业前后对比）：

```
## 记忆变更

### 毕业到 docs（3 条）
- feedback_redis-pool-exhaustion.md → docs/faq-troubleshooting.md「Redis 连接池打满」
  原因：同一主题教训出现第 3 次，已是稳定知识
- project_auth-migration.md → docs/architecture.md「认证模块迁移」
  原因：事件记录，决策结论进 docs，过程进 git log
- reference_env-vars.md → CLAUDE.md 环境变量表
  原因：本属"系统怎么工作"，memory 顶多留指针

### 精简结果
- MEMORY.md：80 行 → 22 行（保留 3 条 reference 指针 + 1 条近期 feedback）
- docs/faq-troubleshooting.md：新增「Redis 连接池打满」章节
- docs/architecture.md：新增「认证模块迁移」章节

### 体量倒挂检查
✅ memory 目录总体积 < docs/ 总体积（健康态）
```

## 它和同类有什么不同？

| 维度 | 记忆持久化类 Skill | neat-freak |
|------|-------------------|------------|
| **核心动作** | 写入记忆（捕获→存储→检索注入） | 审查对齐（比对→修正→精简） |
| **时序** | 会话中捕获 | 会话后审查 |
| **产物** | 持久化记忆库 | 与代码一致的文档 + 精简记忆 |
| **依赖** | 需要存储/检索基础设施 | 零依赖，靠 Agent 自身能力 |
| **解决的问题** | "AI 失忆" | "记住的东西对不对" |

同类 Skill（claude-mem、agentmemory、ultra-memory、ai-memory）都在解决"怎么记住"，neat-freak 解决"记住的东西对不对"。

## 安全边界

- **只修改文档和记忆文件**，不碰代码
- **初始化时必须用户确认**后才执行操作清单
- **常规同步自动执行**，但记忆出现无法自动判断的矛盾时暂停问用户
- **删除记忆文件前**会列出清单，不静默删除
- **全局配置极度克制**——只有用户明确表达跨项目核心原则时才动 `~/.claude/CLAUDE.md`

## 文件结构

```
neat-freak-skills/
├── skill/                              # Skill 运行时文件（Agent 读取的文件）
│   ├── SKILL.md                        # 技能主文件（流程、原则、触发条件）
│   └── references/
│       ├── doc-standards.md            # 文档规范基线（CLAUDE.md/AGENTS.md/README.md/docs/ 各板块标准）
│       ├── sync-matrix.md              # 变更影响矩阵（变更类型 → 要改哪些文件）
│       ├── agent-paths.md              # 各 Agent 记忆与配置路径速查
│       └── init-report-template.md     # 初始化审查报告模板
├── docs/                               # 面向人类的文档
│   ├── user-guide.md                   # 用户手册（安装、触发、使用流程、FAQ）
│   └── technical-manual.md             # 技术手册（架构、流程机制、扩展指南）
├── test-prompts.json                   # 测试样例（3 个典型场景）
├── CHANGELOG.md                        # 变更日志
└── LICENSE                             # MIT 协议
```

## 文档

| 文档 | 内容 |
|------|------|
| [用户手册](docs/user-guide.md) | 安装、触发方式、两种模式使用流程、交付物解读、FAQ |
| [技术手册](docs/technical-manual.md) | 设计哲学、流程引擎内部机制、关键机制详解、测试协议、扩展指南 |

## 验证与测试

见 [test-prompts.json](test-prompts.json)——包含 3 个典型测试场景：

1. **init-new-project**：初始化新项目（验证初始化流程 + 语义触发）
2. **sync-after-feature**：功能开发后同步（验证常规同步 + 变更影响识别）
3. **colloquial-trigger**：口语化触发（验证语义匹配不漏触发）

每个场景包含 `expected_behavior`（期望行为）和 `verification_points`（验证点），可用于 dry_run 评估。

## License

[MIT](LICENSE)

<!-- neat-freak: initialized at 2026-06-20 -->
