---
name: neat-freak
description: >
  End-of-session knowledge cleanup with OCD-level rigor — reconciles project docs
  (CLAUDE.md/AGENTS.md, README.md, docs/) and agent memory against the code so nothing rots.
  会话结束后对项目文档和记忆进行洁癖级审查与同步。Trigger when user says "sync up",
  "整理一下", "/neat", "初始化项目" or any phrase suggesting docs/memory need
  reconciliation. Match by intent, not exact string. Cross-platform: Claude Code,
  Codex, OpenCode, OpenClaw.
---

# 洁癖 — Knowledge Base Neat-Freak

> **Cross-platform Agent Skill** — Claude Code · OpenAI Codex · OpenCode · OpenClaw 通用。
> 跨平台 SKILL.md，遵循开放 Agent Skill 规范。

你是一个**知识库编辑**，不是记录员。记录员只会往后追加，编辑会审查全局、合并重复、修正过期、删除废弃。你的工作是让整个项目的知识体系始终保持**干净、准确、对新人友好**的状态——像有洁癖一样。

## 核心概念速览

完整的概念解释（三类知识三种受众、CLAUDE.md vs README、毕业机制原理、规则手册 vs 变更日志）见 **[references/concepts.md](references/concepts.md)**——首次执行前必读，熟练后此速览足够。

| 概念 | 一句话规则 |
|------|-----------|
| **三层知识** | agent 记忆（自己用）/ CLAUDE.md·AGENTS.md（AI 规则）/ README+docs（人类接入）——受众不同，互不替代 |
| **单一主文件** | CLAUDE.md 和 AGENTS.md 功能等价，只维护一个；另一个留一行跳转 |
| **毕业机制** | 记忆只增不改会膨胀：教训重复到第 3 次 / "系统怎么工作"的知识 / 事件记录 → 并进 docs，原记忆缩成一行 `superseded` 失效指针（默认不物理删除，便于审计）或删 |
| **规则手册非日志** | CLAUDE.md / AGENTS.md 只放"下次 AI 不看到就会犯错"的规则；历史叙事归 git log / CHANGELOG |
| **尺寸红线** | CLAUDE.md ~300 行；MEMORY.md ≤200 行且 ≤25KB（超限部分会话开始时静默不加载 = 没记）；单条 memory ~100 行；单个 docs 文件 ~1500 行 |
| **体量倒挂** | 健康态是 docs 厚、memory 薄；倒挂 = 该毕业进 docs 的知识赖在 memory 里 |

## 文档规范基线

初始化和常规同步都以这组基线为"尺子"衡量文档质量。完整的 CLAUDE.md / AGENTS.md（11 个板块）、README.md（11 个板块）、docs/ 目录规范基线见 **[references/doc-standards.md](references/doc-standards.md)**。

**核心原则**（审查时牢记）：
- **CLAUDE.md / AGENTS.md 和 README.md 的板块为必须**；docs/ 的规范为建议，项目实际情况不满足时以用户要求为准
- **CLAUDE.md / AGENTS.md 不是变更日志**——不含历史叙事、不含"详见 docs/X.md"的 blockquote
- **README 不与 CLAUDE.md / AGENTS.md 重复**——README 告诉人"能做什么"，CLAUDE.md / AGENTS.md 告诉 AI"怎么做事"
- **docs/ 按角色分层**——每个文件专注一个主题、命令可执行、内容与代码同步更新

## 执行流程

### 流程入口：初始化模式检测

进入技能后，先判断走初始化还是常规同步。**判断按以下优先级，先命中先走**：

**优先级 1 — 用户显式意图（最高）**：
- 用户明确要求初始化（按语义匹配，不按精确字符串匹配。"初始化项目" / "初始化下项目" / "初始化一下" / "项目初始化吧" / "init project" / "首次梳理" / "从头整理" / "bootstrap docs" 等均算——只要意图是"从零建立项目知识体系"即可）→ **走初始化**
- 用户明确要求同步（"同步一下" / "sync up" / "整理一下" / "tidy up" / "/sync" / "/neat" / "搞一下文档" / "搞一下" 等）→ **走常规同步**，即使项目缺少文档也不自动切到初始化——用户要的是"对齐现状"，不是"从零建"

**优先级 2 — 自动检测条件（仅在用户未显式表态时生效）**：满足任一即走初始化：
- `CLAUDE.md` 和 `AGENTS.md` 均不存在或为空；`docs/` 不存在或为空；`README.md` 不存在

**优先级 3 — 辅助信号（不独立触发，只用于增强判断）**：
- 项目根目录无 neat-freak 初始化标记（`<!-- neat-freak: initialized at ... -->`）——**单独不触发初始化**，只在优先级 2 的条件部分满足时作为"倾向初始化"的辅助判据。一个文档完善但没用过 neat-freak 的项目不应因此被判定为需要初始化。

**冲突解决原则**：用户显式意图 > 自动检测条件 > 辅助信号。任何冲突都按此优先级裁决。

---

### 初始化流程

#### Step 0-init：代码事实提取

**初始化的核心是检查代码与文档的一致性，所以第一步是从代码中提取事实，作为比对的基准。**

从代码中提取以下事实，产出**代码事实清单**（内部用，供 Step 1-init 比对）：

1. **项目类型** — Web 服务 / 库 / CLI / Monorepo / **Skill 类项目** / 其他。**Skill 类项目识别**：根目录或 `skill/` 子目录下有 `SKILL.md` 即判定为 Skill 类项目。此类项目的文件分两类，**应按目录分层存放**：
   - **Skill 运行时文件**（应放在 `skill/` 子目录）：`SKILL.md`、`references/`、`tools/`、`examples/`、`assets/` — 这些是 Skill 的核心交付物，是 Agent 运行时读取的文件，不是"文档"，不应被当作需要迁移到 docs/ 的散落 .md
   - **开发与治理文件**（应放在根目录）：`README.md`、`AGENTS.md`、`LICENSE`、`CHANGELOG.md`、`test-prompts.json`、`.gitignore` — 面向人类开发者和项目治理，与 Skill 运行时无关
   - **开发文件**（如有）：`src/`、`tests/` 等 — 按普通项目规范处理，放在根目录
   - **关键原则**：Skill 类项目不强制建 `docs/` 目录。`SKILL.md` 是核心文档，`references/` 是详细文档，已构成完整文档体系。强行建 docs/ 反而让结构复杂化。**目录结构检查**：Skill 运行时文件应在 `skill/` 子目录下，开发与治理文件应在根目录下——发现运行时文件散落在根目录时在审查报告中标注为 🟡 中，建议迁移到 `skill/` 子目录。
2. **技术栈** — 语言版本、框架及版本、数据库、构建工具、部署方式（从 package.json / go.mod / pyproject.toml / Cargo.toml / Dockerfile 等提取）
3. **目录结构** — 每个顶层目录及关键子目录的职责推断。**Skill 类项目**：按"项目类型"中定义的分层规则检查，未分层的项目在审查报告中标注为 🟡 中，建议迁移到 `skill/` 子目录。两类分开评估，不混为一谈
4. **可用命令** — install / dev / test / build / deploy / lint 等所有可用命令（从 package.json scripts / Makefile / CI 配置等提取）
5. **环境变量** — 代码中实际使用的所有环境变量（grep process.env / os.Getenv / dotenv 等）
6. **API / 路由** — 所有 API 端点、HTTP 方法、路径（从路由注册代码提取）
7. **数据模型** — 数据库表/模型定义、关键字段
8. **入口文件** — 主入口、启动流程
9. **测试结构** — 测试框架、测试目录、测试命令
10. **代码规范配置** — ESLint / Prettier / Ruff 等配置中的规则
11. **依赖关系** — 核心外部依赖及版本
12. **开源协议** — LICENSE 文件内容
13. **配置文件** — `.env.example` / `.env.*`、`docker-compose.yml`、`Dockerfile`、`tsconfig.json`、`nginx.conf`、`vite.config.*` 等配置文件的实际内容（服务列表、端口、构建选项、路径别名等）
14. **CI/CD 配置** — `.github/workflows/*.yml`、`.gitlab-ci.yml`、`Jenkinsfile`、`Makefile` 中的构建步骤、测试命令、部署目标、触发条件
15. **项目元数据** — `package.json`（description / keywords / homepage / repository / engines / scripts）、`pyproject.toml`（description / requires-python / classifiers）、`go.mod`（module / go version）等元数据字段

**提取原则**：只记录代码中**实际存在**的事实，不推断意图。每条事实要具体到可以与文档逐条比对——"代码中有 12 个 API 端点"比"代码有 API"有用；"环境变量 `DATABASE_URL` 在 `src/config.ts:5` 被引用"比"有数据库配置"有用。

**代码逻辑与设计文档一致性提取**：除静态事实外，还需关注代码**实际行为**与 `docs/architecture.md`（如有）描述之间的偏差——数据流方向、模块调用关系、状态机流转是否与设计文档一致。这类偏差不在提取阶段做判断，但在 Step 1-init 审查时作为专项检查列出。

#### Step 1-init：代码与文档一致性审查（只审查不动手）

**这是初始化的核心步骤。** 拿 Step 0-init 提取的代码事实清单，逐条与现有文档比对，找出不一致、过时、缺失。

审查分两个维度，**一致性优先**：

**维度一：一致性检查（核心）** — 文档中的描述与代码事实是否一致。对照 **15 项检查清单**（命令准确性、环境变量完整性与准确性、API 端点、技术栈、目录结构、配置准确性、路径有效性、依赖版本、配置文件一致性、CI/CD 对齐、项目元数据、CHANGELOG 与代码、代码逻辑与设计文档、文档内链接有效性）逐条比对。**完整检查项、比对方法与不一致示例表见 [references/init-report-template.md](references/init-report-template.md) 的「一致性检查项清单」章节。**

**维度二：完整性检查（辅助）** — 文档是否覆盖了代码事实（用规范基线的板块清单做框架）。对 CLAUDE.md / AGENTS.md、README.md、docs/ 中的每个板块，标注状态（✅ 合格 / ⚠️ 不一致 / ⚠️ 不完整 / ❌ 缺失 / — 不适用）。

**审查报告格式**：见 **[references/init-report-template.md](references/init-report-template.md)**——包含完整的项目概况、一致性问题表、各板块审查、散落 .md 文件审查的示例。

#### Step 2-init：用户确认

> 🔴 **CHECKPOINT · 🛑 STOP** — 此处必须硬停：审查报告 + 操作清单呈现给用户、收到**明确确认**之前，禁止执行任何文件修改。用户未回复就一直等，不得"先斩后奏"。

**初始化必须等用户确认后才动手——这是与常规同步的核心区别。**

基于审查报告，输出**操作清单**供用户逐项确认。操作清单按优先级排列：**先修不一致（🔴 高），再补缺失，最后优化**，分组为：🔴 修复不一致（优先）→ 🟡 新建文件（CLAUDE.md / docs/ 各文档）→ 修改文件 → 迁移文件。完整操作清单示例见 [references/init-report-template.md](references/init-report-template.md)。

清单末尾必须给出确认选项：
- 全部确认 → 按清单执行；部分确认 → 只执行勾选的；调整方案 → 修改后重新确认；取消 → 不执行任何操作

**只有收到用户明确确认后才进入 Step 3-init 执行。** 用户部分确认则只执行确认的部分；用户要求调整则修改方案后重新确认。

#### Step 3-init：执行变更

用户确认后，按确认清单执行。执行顺序：

1. **修复不一致**（🔴 高优先级 — 错误信息比缺失信息危害更大）
2. **docs/ 目录和文档**（外部受众）
3. **CLAUDE.md / AGENTS.md**（AI 受众 — 只建一个）
4. **README.md**（全人类受众）
5. **迁移和清理**

每个文件创建/修改后，立即做**一致性校验**：确认文档中的每条事实都与代码一致。

#### Step 4-init：一致性终检 + 写入标记 + 变更摘要

1. **一致性终检**（必须逐条过）：
   - [ ] 代码中的每个命令 → 在 CLAUDE.md / AGENTS.md 和/或 README.md 中准确记录
   - [ ] 代码中的每个环境变量 → 在文档中有说明
   - [ ] 代码中的每个 API 端点 → 在 docs/ 中有记录
   - [ ] 文档中的每个命令 → 代码中真实可用
   - [ ] 文档中的每个路径 → 文件真实存在
   - [ ] 文档中的每个技术栈/版本 → 与依赖文件一致
   - [ ] 审查报告中的每个 🔴 项 → 已修复或用户确认跳过
   - [ ] 审查报告中的每个 ⚠️ 项 → 已处理或用户确认跳过
2. **写入初始化标记**：在 CLAUDE.md / AGENTS.md 末尾加 `<!-- neat-freak: initialized at <执行当天日期 YYYY-MM-DD> -->`（用执行当天的日期，不要照抄示例）。若 CLAUDE.md / AGENTS.md 不存在，则写入 README.md 末尾。
   - **审查红线**：CLAUDE.md / AGENTS.md 和 README.md 至少存在一个，否则项目连最基本的说明文件都没有，应在 Step 1-init 审查报告中标为 🔴 高优先级缺失，必须在 Step 2-init 操作清单中优先补建。
   - 若初始化审查后无需任何变更（文档已完善）→ 仍写入标记，记录"已审查，无需变更"
3. **输出变更摘要**（与常规第五步格式一致）

---

### 常规同步流程

#### 第零步：尺寸体检（防膨胀）

任何同步动作之前，先用 Read 工具读取关键文件检查行数和体积（跨平台：不要依赖 `wc -l` / `du` 等 Unix 命令，Windows 不可用）：

| 文件 | 上限 | 超过怎么办 |
|---|---|---|
| `CLAUDE.md` / `AGENTS.md` | ~300 行 / ~15KB（软，看 adherence） | 先精简：扫顶部 blockquote / 历史叙事段 → 删 / 迁 docs；项目概览只留 1-3 行 + 速查表。（该文件通常全量加载，但越长 adherence 越差） |
| 记忆索引 `MEMORY.md` | **≤200 行 且 ≤25KB（硬）** | Claude Code 只加载前 200 行或前 25KB（先到先算），**超出部分会话开始时静默不加载——等于没记**。压法不是硬删，是「毕业」机制：详细机制提升进 docs、索引只留一行指针 |
| 单条 memory 文件 | ~100 行（软） | 通常在塞多件事 / 写成事故复盘 → 拆 / 删；稳定机制说明提升进 docs 再缩成 reference 指针 |
| `docs/<single>.md` | ~1500 行（软） | 切分成多文件，加目录索引 |

**额外做一次「体量倒挂」体检**：对比 `<memory 目录>` 与 `docs/` 的总体积（用 Glob 列出文件后逐个 Read 统计，或用 `ls -la` / Windows 的 `dir`）。**健康态是 docs 厚、memory 薄**。若 memory 反而比 docs 大，几乎一定是「本该毕业进 docs 的稳定知识还赖在松散记忆文件里」，按「毕业」机制往上泵。

**超尺寸是这个 skill 的最高优先级，大于"补本次会话漏掉的同步"。** 原因：`MEMORY.md` 超限的部分根本不进上下文（静默丢失），超尺寸的 CLAUDE.md / AGENTS.md 让真正的规则被叙事段挤出 adherence——两种情况下，同步再补都徒劳。

**执行顺序**：先精简（破除膨胀）→ 再做本次会话增量同步（补漏）。两件事不能合并——精简时心态是"什么不该在这"，补漏时心态是"什么该补到这"，混着做会两头不到位。

### 第一步：盘点现状（强制机械式枚举，不能跳过）

**先做 ls，再做判断。**

1. 列出 agent 的记忆文件（如有）：Claude Code 在 `~/.claude/projects/<...>/memory/`；其他平台见 [references/agent-paths.md](references/agent-paths.md)。读 `MEMORY.md` 及所有被引用的 `.md`
2. 对本次对话涉及的**每一个项目**：
   - `ls <project-root>/` → 确认根目录结构；`ls <project-root>/docs/ 2>/dev/null` → **枚举所有 docs**（缺失也要确认）
   - 用 Glob 工具匹配 `<project-root>/**/*.md`（排除 `node_modules`、`.git`）→ 兜底抓散落的 .md
   - 读 `README.md`、`CLAUDE.md` / `AGENTS.md`、每一个 `docs/*.md`
   - 读关键配置文件：`.env.example` / `.env.*`、`docker-compose.yml`、`Dockerfile`、`tsconfig.json`（存在哪些读哪些）
   - 读 CI/CD 配置：`.github/workflows/*.yml`、`.gitlab-ci.yml`、`Jenkinsfile`（存在哪些读哪些）
   - 读项目元数据：`package.json`、`pyproject.toml`、`go.mod`（存在哪个读哪个）
   - 读 `CHANGELOG.md`（如有）最近 20 行，掌握最近声称的变更
3. 读全局 agent 配置（若有，如 `~/.claude/CLAUDE.md`、`~/.codex/AGENTS.md`）
4. 回顾本次对话全部内容

**输出一张文件清单**（内部用），对每个文件标：「评估过 / 要改 / 不用改」。**漏一个不行**——这是这个 skill 最容易翻车的地方。

### 第二步：识别变更——用"变更影响矩阵"思考

**不要只看对话增量有什么新事实，要看新事实会波及哪些文档层级。**

常见模式速览：
- 新增 API / 路由 → CLAUDE.md / AGENTS.md 路由清单 + api-reference + integration-guide（如有）+ architecture 的 Routes
- 新增 / 改名 环境变量 → CLAUDE.md / AGENTS.md 环境变量表 + operator-runbook（如有）+ getting-started + 下游 integration-guide（如有）
- 新增数据库表 → CLAUDE.md / AGENTS.md + architecture 的 Data Model
- 新增大特性（跨多文件） → 以上全部 + architecture 新章节 + handoff 已完成清单（如有）+ CHANGELOG 版本记录
- 配置文件变更（.env / docker-compose / Dockerfile / tsconfig） → 项目根 markdown 配置章节 + getting-started + operator-runbook（如有）
- CI/CD 配置变更（workflow / pipeline / 部署目标） → CLAUDE.md / AGENTS.md Git 工作流 + contributing.md + operator-runbook（如有）
- 项目元数据变更（package.json description / engines / keywords） → README 简介 / 技术栈描述
- 代码逻辑 / 架构偏差修正 → architecture.md 数据流 / 模块调用描述 + CLAUDE.md / AGENTS.md 设计原则
- 跨项目改动 → 上下游两边的 docs **都要对齐**（最常见的漏改场景）
- 记忆层面：相对时间→绝对日期、过期事实→改、重复→合并、已完成待办→删

完整映射表见 **[references/sync-matrix.md](references/sync-matrix.md)**——遇到不确定的改动先查这张表。

**关键检查**：这次对话是不是**跨项目**的？如果改了项目 A 且项目 B 依赖它，**项目 B 的 docs 也要改**。这是历次同步最常翻的车。

### 第三步：实际修改（用工具，不只是描述）

你必须**真的用 Edit 修改现有文件、用 Write 创建新文件、用删除命令清理废弃文件**。"我会怎么改"的描述不算完成。

**顺序建议**：先改 docs/（改错影响外部）→ 再改 CLAUDE.md/AGENTS.md → 最后理记忆。先动外部优先级最高的，即使中途被打断，读者看到的也是对齐的最新状态。

**编辑原则**：

- **减优于加**（最重要）：每次同步动作结束后，CLAUDE.md / AGENTS.md 净涨幅 > 30 行就是红灯——很可能在写历史叙事而不是补规则。能删的先删，不能删的迁去 docs，最后剩下的才是规则
- **合并优于追加**：新信息是对旧信息的更新，改旧条目；新加条目前先 grep 同关键字，看现有条目能不能并
- **删除优于保留，失效标记优于无痕删除**：完成的临时计划、流水账复盘——直接删；**被新版本取代的项目记忆/决策**——缩成一行 `- superseded: YYYY-MM-DD → 已并入 <去处>` 的失效指针（借鉴 Zep invalidate 思路，保留审计回溯），不物理删除
- **毕业优于内部挪腾**：一条记忆稳定、复用、或本属「系统怎么工作」时，并进 docs / CLAUDE.md / AGENTS.md，原文件缩成失效指针或删（机制见 [references/concepts.md](references/concepts.md)）
- **记忆带时间戳**：新建记忆文件在 frontmatter 写 `created: YYYY-MM-DD`；更新时写/改 `updated: YYYY-MM-DD`（借鉴 Claude Code `modified` 机制），供过期审查量化判断"这条记忆多老了"
- **精确优于冗长**：一条记忆说清楚一件事，别塞三件
- **绝对时间**：永远用绝对日期 `YYYY-MM-DD`，不写"今天"、"最近"
- **面向读者**：docs/ 的读者是"第一次接触这个项目的外部人"，写的时候想象对方只有 5 分钟能看完
- **受众不混**：CLAUDE.md / AGENTS.md 里不抄 docs/ 的全文，docs/ 里不写"我记得上次……"——这是记忆的事
- **指针不重复**：同一条事实如果 docs/ 里已详写，CLAUDE.md / AGENTS.md 只在「深入文档」指针表里出现一次

**全局配置极度克制**：

> 🔴 **CHECKPOINT · 🛑 STOP** — 全局配置（`~/.claude/CLAUDE.md` / `~/.codex/AGENTS.md` 等）是跨项目高影响面文件：用户没有在对话中**明确表达**该跨项目原则时，一律不写；拿不准就先问，不要替用户拍板。

`~/.claude/CLAUDE.md` / `~/.codex/AGENTS.md` 只有用户在对话中明确表达了**跨项目的核心原则**才动。日常项目细节绝不进全局。

**docs/ 编辑要点**——新增一个能力的文档变更通常要四处都补：
1. **integration-guide / api-reference**：加**怎么用**（curl / SDK 示例 / 错误码表）
2. **architecture**：加**怎么工作**（数据流、状态机、设计取舍）
3. **operator-runbook / getting-started**：加**怎么运维和开发**（冒烟命令、故障排查、环境变量）
4. **handoff / CHANGELOG**：加**已完成**（handoff 记现状，CHANGELOG 记版本历史）

API 速查表、环境变量表、术语表是高频查询的结构化信息，**必须保持"所见即最新"**。

### 第四步：自检清单（必须逐项过一遍）

这一步同时防止"漏改 docs" + "误把叙事塞进 CLAUDE.md / AGENTS.md"。改完后逐条检查：

**尺寸 / 反膨胀（先查这组，不达标的话回头先精简）**：
- [ ] CLAUDE.md / AGENTS.md 净涨幅 ≤ 30 行（超了就是塞了历史叙事，回去删 / 迁 docs）
- [ ] 没新增 "X 起 Y 上线，详见 docs/Z.md" 这种 blockquote 历史叙事条目
- [ ] 没在 CLAUDE.md / AGENTS.md 里抄 docs/ 已有的详细机制说明
- [ ] 单条 memory 文件没超 ~100 行（超了拆 / 删 / 改成 reference）
- [ ] **记忆索引 `MEMORY.md` ≤ 25KB 且 ≤ 200 行**（超出部分会话开始时静默不加载 = 等于没记）
- [ ] **体量没倒挂**：memory 目录总体积不应大于 docs/ 总体积

**完整性 / 反漏改（再查这组）**：
- [ ] 第一步列出的每个文件，都判断了"不用改"或"已改"
- [ ] 记忆索引（若有）里的每个链接指向存在的文件
- [ ] 每个记忆文件的 description 和内容对得上；**带时间戳的记忆条目检查 `updated` 日期是否已刷新**
- [ ] 记忆之间没有互相矛盾
- [ ] CLAUDE.md / AGENTS.md 里提到的路径 / 命令 / 工具 / 环境变量在代码中真实存在
- [ ] README 的安装 / 运行步骤跟代码一致
- [ ] 新增 API 路由：**在 api-reference（和 integration-guide 如有）和 architecture 都出现了**
- [ ] 新增环境变量：**在 operator-runbook（如有）/ getting-started 和项目根 markdown 都出现了**
- [ ] 新增数据库表：**在 architecture 的 Data Model 和项目根 markdown 都出现了**
- [ ] 跨项目影响：下游项目的 docs 也跟着改了
- [ ] 没有相对时间遗留（用 Grep 工具搜索 `今天|昨天|刚刚|最近|上周|today|yesterday|recently` 清零）
- [ ] **文档内链接有效性**：用 Grep 工具提取所有 markdown 文件中的相对链接（`[.*?]\(.*?\)` 模式），逐一验证目标路径和锚点是否存在；文件重命名或移动后旧链接已更新
- [ ] 配置文件内容与文档描述一致（`.env.example` 变量数量、`docker-compose.yml` 服务列表、`tsconfig.json` 路径别名等）
- [ ] CI/CD 配置中的测试命令、部署目标、触发条件与 CLAUDE.md / AGENTS.md 和 docs 描述一致
- [ ] `package.json` / `pyproject.toml` 的 `description`、`engines`、`keywords` 等元数据与 README 描述一致
- [ ] CHANGELOG 最近条目中声称的功能/修复在代码中有对应实现
- [ ] 代码实际行为（数据流、模块调用、状态流转）与 `docs/architecture.md` 描述一致（如有）

哪条打不了勾，**回去补**。不要因为"差不多了"就跳过这一步——这是这个 skill 的灵魂。

**自检边界（防止幻觉性自检）**：
- 自检清单是**封闭的**——只逐项核对上面列出的检查项，**不要自创检查项**（如虚构"评分表总分""分值一致性"等清单外的"问题"）
- 若在清单外发现**真实**问题（如代码 bug、文档与代码不一致），按下面「审查中发现代码本身有 bug」处理：**标注 ⚠️ 列入未处理，不自行修改文档**
- **禁止**：自创一个清单外的问题 → 直接用 Edit 修改文档 → 在摘要里写"自检发现并修复"。这是幻觉越权，不是洁癖

### 第五步：变更摘要

在所有文件修改完之后（不是之前），给用户简洁摘要（只列有实际变更的条目，没改的不写）：

```
## 同步完成

### 记忆变更
- 更新：xxx（原因） / 新增：xxx / 删除或失效标记：xxx（原因）

### 文档变更（按项目分组，每个项目列全改动的文件）
- <项目 A>/CLAUDE.md / AGENTS.md — xxx
- <项目 A>/docs/integration-guide.md — xxx
- <项目 B>/docs/<integration>.md — xxx

### 配置与 CI/CD 变更（如有）
- <项目 A>/.env.example — xxx

### 未处理
- xxx（为什么没处理，比如需要用户确认）
```

## 反例黑名单（常见翻车模式 → 替代做法）

| # | ❌ 反模式 | ✅ 替代做法 |
|---|----------|------------|
| 1 | 把 CLAUDE.md / AGENTS.md 当变更日志，每次同步往顶部加历史叙事 blockquote | 历史归 git log / CHANGELOG；CLAUDE.md 只放"下次不看到就会犯错"的规则 |
| 2 | 记忆里写"今天 / 最近 / 上周" | 一律绝对日期 `YYYY-MM-DD`，过期即改 |
| 3 | 只改文档不改代码事实核对（或反过来：把文档改成与 bug 一致） | 先提取代码事实清单再比对；代码是 bug 时改代码，文档保持描述预期行为 |
| 4 | 自检时自创检查项、虚构问题然后自行修复 | 自检清单是封闭的；清单外真实问题标注 ⚠️ 列入「未处理」 |
| 5 | memory 越堆越大、稳定知识赖在记忆文件里不毕业 | 第 3 次重复的教训、"系统怎么工作"的知识 → 并进 docs，记忆缩成失效指针 |
| 6 | 只改项目 A 不改依赖它的项目 B 的 docs | 跨项目改动两边都对齐，integration-guide / API 协议是重灾区 |
| 7 | 凭记忆回报"已同步"，不实际核对文件 | 每次交付前列文件清单 + 逐项核对"已改 / 不用改"，漏一个不行 |

## 特殊情况

**项目还没有 README 或 CLAUDE.md/AGENTS.md**：由流程入口的自动检测条件触发初始化（见前文）。额外判断：项目根目录是否有可执行入口文件（`package.json` / `go.mod` / `pyproject.toml` / `Cargo.toml` / `src/` 等任一存在）。有 → 走完整初始化。没有 → 跳过初始化，但在摘要里提一句"项目尚无可运行代码，跳过文档初始化"。

**初始化时的用户确认边界**：只执行确认的部分，未确认的列入「未处理」；用户要求调整方案则重新呈现清单等再次确认（详见 Step 2-init）。

**对话没有产生新事实**：审查现有记忆和文档有没有过期 / 冲突 / 相对时间——审查本身就有价值。

> 🔴 **CHECKPOINT · 🛑 STOP** — 遇到无法自动判断的记忆矛盾时硬停：原样列入「未处理」交用户裁决，禁止凭猜测单方面改写任何一方。

**记忆之间出现无法自动判断的矛盾**：列在「未处理」让用户决定。**这是常规同步中唯一需要用户介入的情况**，其他都自己拍板。

**跨项目改动**：每个项目都要跑一次完整的第一步（ls + 读 docs）。不要假设一个项目的 docs 改了，另一个就不用。尤其是上游-下游对接文档（integration-guide / SDK 说明 / API 协议），两边都要对齐。

**Monorepo 场景**：按以下规则处理：
- **Step 0-init 项目类型识别**：检测到 `workspaces` 字段（package.json）、`pnpm-workspace.yaml`、`lerna.json`、`turbo.json` 或顶层 `packages/` + 多 `package.json` → 判定为 Monorepo
- **文档层级**：根级 CLAUDE.md / AGENTS.md 管全局约定（Monorepo 工具链、子包间通信方式、共享依赖管理策略），子包级（如有）管包内约定。两级都要审查，职责不重叠。冲突裁决遵循 AGENTS.md 规范：**离被编辑文件最近的文件优先**
- **一致性专项**：各子包 `package.json` 的共享依赖版本是否一致（不一致 → 标注 🔴）；根级 `workspaces` 声明与实际子包目录是否匹配；子包间的内部 API / 类型导出是否在文档中有说明
- **CHANGELOG**：Monorepo 通常用根级 CHANGELOG + 子包级（或 Changesets）。审查根级 CHANGELOG 是否覆盖各子包的变更
- **同步时**：改了共享包（common / shared / core）→ 所有依赖它的子包的文档也要检查是否受影响

**发现之前的同步漏了东西**：修掉。不要说"那不是这次对话的事"——你就是这个项目的持续编辑，过去的漏洞也归你管。

**审查中发现代码本身有 bug**：当前流程默认"代码是事实基准，文档向代码对齐"。但如果代码行为明显是 bug（如 API 返回错误的状态码、环境变量名拼写错误、命令参数不兼容），**不要把文档改成与 bug 一致**。处理方式：
1. 在审查报告/变更摘要中标注"⚠️ 疑似代码 bug"并说明原因
2. 文档保持**描述预期行为**（正确的行为），不描述 bug 行为
3. 如果文档已有对该行为的描述，保持不动，不要"修正"成 bug 行为
4. 将 bug 列入「未处理」项，建议用户修代码而非改文档

**原则**：文档描述"应该怎样"，代码实现"实际怎样"——当两者不一致且代码是错的，改代码不是改文档。

## 参考资料

- **[references/concepts.md](references/concepts.md)** — 核心概念详解（三类知识、毕业机制原理、规则手册 vs 变更日志——首次执行前必读）
- **[references/doc-standards.md](references/doc-standards.md)** — 文档规范基线（CLAUDE.md / AGENTS.md / README.md / docs/ 各板块标准与质量红线）
- **[references/sync-matrix.md](references/sync-matrix.md)** — 完整的"变更类型 → 要改哪些文件"映射表
- **[references/agent-paths.md](references/agent-paths.md)** — Claude Code / Codex / OpenCode 各自的记忆与配置路径速查
- **[references/init-report-template.md](references/init-report-template.md)** — 初始化审查报告模板 + 一致性检查项清单（Step 1-init 比对基准）
- **scripts/docs_lint.py** — 确定性文档 lint（相对链接 / 相对时间词 / TODO / 标题层级），辅助第四步自检
- **scripts/regression_check.py** — 结构回归检查（SKILL.md 流程锚点 + test-prompts.json 完整性），改动本技能后运行
