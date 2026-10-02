# neat-freak 技术手册

> 面向开发者和贡献者的内部机制说明：架构设计、流程引擎、关键机制与扩展指南。
> 使用层面的安装与操作见 [用户手册](user-guide.md)。

## 1. 设计哲学

neat-freak 的全部机制建立在四个设计判断上：

1. **代码可以随时重写，文档和记忆是跨会话、跨 Agent 的唯一桥梁**。记忆里的过期信息会让下一个 Agent 基于错误前提做决策——这是比"没有文档"更隐蔽的危害。
2. **三类知识、三种受众**。Agent 记忆（受众：Agent 自己）、CLAUDE.md / AGENTS.md（受众：项目内的 AI）、docs/ + README（受众：人类同事与下游开发者）。三层受众不同、职责不同，同步时必须分别处理，只改 CLAUDE.md 就结束是最常见的翻车模式。
3. **记忆只增不改、docs 就地编辑的不对称**。docs 靠就地编辑天然收敛；agent 记忆天生只追加，没有反向阀门必然膨胀到比 docs 还大。反向阀门就是"毕业"机制（§4.4）。
4. **CLAUDE.md / AGENTS.md 是规则手册，不是变更日志**。历史叙事进 git log / CHANGELOG；判断一条信息是否该进规则手册的标准是："下次 AI 写代码时如果没看到这条，会不会犯错？"

## 2. 文件结构与组件职责

```
neat-freak-skills/
├── skill/                              # Skill 运行时文件（Agent 读取）
│   ├── SKILL.md                        # 主引擎：流程定义、原则、触发条件（~37KB）
│   └── references/                     # 按需加载的参考模块
│       ├── doc-standards.md            # 文档规范基线（CLAUDE.md 11 板块 / README 11 板块 / docs/ 规范）
│       ├── sync-matrix.md              # 变更影响矩阵（变更类型 → 应改文件 的完整映射表）
│       ├── agent-paths.md              # 各平台记忆与配置路径速查（Claude Code / Codex / WorkBuddy / OpenClaw / OpenCode）
│       └── init-report-template.md     # 初始化审查报告模板（Step 1-init 输出格式）
├── docs/                               # 面向人类的文档（本目录）
├── test-prompts.json                   # 测试协议（3 场景 + expected_output 断言）
├── README.md / CHANGELOG.md / LICENSE  # 项目治理文件
```

**设计要点**：运行时文件（`skill/`）与治理文件（根目录）分层存放。SKILL.md 是核心文档，`references/` 是详细文档，两者已构成完整文档体系，因此 Skill 类项目**不强制建 docs/**（本仓库的 docs/ 服务于人类贡献者，不属于运行时依赖）。

## 3. 流程入口：模式判定引擎

进入技能后先判定走初始化还是常规同步，按三级优先级裁决：

```
优先级 1 — 用户显式意图（最高）
  "初始化项目"类语义 → 初始化
  "同步一下"类语义   → 常规同步（即使项目缺文档也不自动切换）

优先级 2 — 自动检测条件（仅在用户未表态时）
  满足任一 → 初始化：
  - CLAUDE.md 和 AGENTS.md 均不存在或为空
  - docs/ 不存在或为空
  - README.md 不存在

优先级 3 — 辅助信号（不独立触发）
  项目根无 neat-freak 初始化标记 → 仅作为"倾向初始化"的辅助判据
```

初始化还有一道可执行入口门槛：项目根有可执行入口文件（`package.json` / `go.mod` / `pyproject.toml` / `Cargo.toml` / `src/` 任一存在）才走完整初始化，否则跳过并在摘要中说明。

## 4. 初始化流程引擎（Step 0-init ~ Step 4-init）

### 4.1 Step 0-init：代码事实提取

以代码为唯一事实基准，提取 15 类事实：项目类型（含 Skill 类项目识别——根目录或 `skill/` 子目录有 SKILL.md 即判定）、技术栈、目录结构、可用命令、环境变量、API/路由、数据模型、入口文件、测试结构、代码规范配置、依赖关系、开源协议、配置文件内容、CI/CD 配置、项目元数据。

**提取原则**：只记录代码中实际存在的事实，不推断意图；每条事实具体到可与文档逐条比对。

### 4.2 Step 1-init：一致性审查（只审不改）

双维度审查：

- **维度一：一致性检查（核心）**——15 项比对，包括命令准确性、环境变量完整性/准确性、API 端点一致性、技术栈准确性、配置文件一致性、CI/CD 与文档对齐、CHANGELOG 与代码一致性、代码逻辑与设计文档一致性、文档内链接有效性等。
- **维度二：完整性检查（辅助）**——按 doc-standards.md 的板块清单逐项标注 ✅ / ⚠️ / ❌。

输出格式由 `references/init-report-template.md` 定义。

### 4.3 Step 2-init：用户确认（硬门槛）

**未经确认不动手**是初始化与常规同步的核心区别。操作清单按 🔴 修复不一致 → 🟡 新建 → 修改 → 迁移排序；用户可全部确认 / 部分确认 / 调整方案 / 取消。

### 4.4 Step 3-init：执行与逐文件校验

执行顺序：修复不一致（🔴 优先，错误信息比缺失信息危害更大）→ docs/ → CLAUDE.md / AGENTS.md（只建一个）→ README.md → 迁移清理。每个文件修改后立即做一致性校验。

### 4.5 Step 4-init：终检与标记

14 项逐条终检；末尾写入初始化标记 `<!-- neat-freak: initialized at <当天日期> -->`（优先 CLAUDE.md / AGENTS.md，否则 README.md）。审查红线：CLAUDE.md / AGENTS.md 和 README.md 至少存在一个，否则标 🔴 并优先补建。

## 5. 常规同步流程引擎（第零 ~ 五步）

### 5.0 第零步：尺寸体检（防膨胀，最高优先级）

| 文件 | 上限 | 超限处理 |
|---|---|---|
| CLAUDE.md / AGENTS.md | ~300 行 / ~15KB（软） | 先精简：删/迁历史叙事 |
| MEMORY.md（记忆索引） | **≤200 行 且 ≤25KB（硬）** | 毕业机制：详述进 docs，索引留指针 |
| 单条 memory 文件 | ~100 行（软） | 拆/删/改 reference |
| docs/ 单文件 | ~1500 行（软） | 切分 + 目录索引 |

**体量倒挂体检**：memory 目录总体积不应大于 docs/ 总体积——倒挂说明该毕业的稳定知识赖在 memory 里。超尺寸是最高优先级，因为 MEMORY.md 超 25KB 的部分在会话开始时**静默不加载**（等于没记），同步再补都徒劳。

### 5.1 第一步：强制机械式枚举

`ls` 项目根 + docs/，用 Glob 兜底抓散落 .md（**不依赖 Unix 专有命令，保证 Windows 可用**），逐个读 README / CLAUDE.md / AGENTS.md / docs / 配置 / CI/CD / 元数据 / CHANGELOG 近 20 行，输出内部文件清单，每个文件标注"评估过 / 要改 / 不用改"。

### 5.2 第二步：变更影响矩阵

核心思想：不看"对话增量"，看"新事实会波及哪些文档层级"。常见映射：新增 API → api-reference + architecture + CLAUDE.md 路由清单；新增环境变量 → CLAUDE.md + getting-started + operator-runbook；跨项目改动 → **上下游两边 docs 都要改**（历次同步最常翻的车）。完整映射查 `references/sync-matrix.md`。

### 5.3 第三步：编辑原则（六条）

1. **减优于加**：同步后 CLAUDE.md 净涨幅 > 30 行即红灯——多半在写历史叙事
2. **合并优于追加**：新信息先 grep 同关键字看能否并入旧条目
3. **删除优于保留**：完成的临时计划、推翻的决策、单次事故流水账——删
4. **毕业优于内部挪腾**：稳定/复用/本属"系统怎么工作"的记忆 → 并进 docs，原文件缩成一行指针或删。毕业判据："**下一个接手的人（不只是我自己）需要知道这件事吗？**"
5. **精确优于冗长 + 绝对时间**：日期永远 `YYYY-MM-DD`，不写"今天/最近"
6. **受众不混 + 指针不重复**：CLAUDE.md 不抄 docs 全文，docs 里不写"我记得上次"

**docs/ 四处补全**：新增能力的文档变更通常要同时补 integration-guide（怎么用）、architecture（怎么工作）、operator-runbook/getting-started（怎么运维开发）、handoff/CHANGELOG（已完成）。

### 5.4 第四步：自检清单（封闭式）

两组检查：**尺寸/反膨胀**（净涨幅、叙事条目、MEMORY.md 体积、体量倒挂）与**完整性/反漏改**（每个文件有判定、链接有效、API/环境变量/数据表在所有应出现的位置出现、跨项目对齐、相对时间清零、CHANGELOG 声明有实现）。

**自检边界（防幻觉防线）**：清单是**封闭的**——禁止自创检查项后直接改文档再报"自检发现并修复"。清单外发现的真实问题（如代码 bug）按"疑似代码 bug"流程：标注 ⚠️ 列入未处理，不修改文档。文档描述"应该怎样"，代码实现"实际怎样"——两者冲突且代码是错的，改代码不是改文档。

### 5.5 第五步：变更摘要

按"记忆变更 / 文档变更（按项目分组）/ 配置与 CI/CD 变更 / 未处理"输出，只列实际变更条目。

## 6. 平台适配层

neat-freak 本身零依赖，靠 Agent 自身工具能力（Read / Glob / Grep / Edit / Write）实现全部动作。平台差异集中在两处：

- **记忆系统位置**：由 `references/agent-paths.md` 速查表适配——Claude Code（`~/.claude/projects/<...>/memory/`）、Codex（无独立记忆，全写 AGENTS.md）、WorkBuddy（`<workspace>/.workbuddy/memory/`）、OpenClaw（`~/.openclaw/`）、OpenCode（扫描 Claude/Codex 目录）。当前 agent 没有独立记忆系统时跳过该层，docs 仍是最低保障。
- **跨平台命令**：SKILL.md 全程避免 `wc -l` / `du` / Unix `find`，改用 Read 工具 / Glob / `dir`，保证 Windows 会话可用。

## 7. 测试协议（test-prompts.json）

`test-prompts.json` 定义 3 个回归场景，每个场景五段式结构：

```json
{
  "id": "场景标识",
  "prompt": "触发语",
  "context": "前置条件",
  "expected_behavior": "期望的流程走向",
  "verification_points": ["人工核对点"],
  "expected_output": {
    "stage": "应停在哪一步",
    "must_contain": ["输出必须包含"],
    "must_not_contain": ["输出必须不含"],
    "example_fragment": "参考输出片段"
  }
}
```

| 场景 | 验证目标 |
|------|----------|
| `init-new-project` | 初始化分支正确进入、语义匹配命中、基于代码事实、Step 2-init 停下等确认 |
| `sync-after-feature` | 常规同步走通、变更影响矩阵识别正确（API→两处、环境变量→两处）、真实修改文件 |
| `colloquial-trigger` | 口语"搞一下文档"能语义触发、正确判断初始化 vs 同步 |

可用于 dry_run 评估：把 `prompt + context` 喂给装好技能的 Agent，对照 `expected_output` 的 must_contain / must_not_contain 断言判定。

## 8. 版本与兼容性

- 当前版本：**0.5.0**（详见 [CHANGELOG](../CHANGELOG.md)）
- 兼容运行时：Claude Code · OpenAI Codex · OpenCode · OpenClaw · WorkBuddy
- 协议：MIT（见 [LICENSE](../LICENSE)）
- 版本演进主线：0.1.0 方法论奠基 → 0.2.0 内容外移 references/ → 0.3.0 审查维度扩充（配置/CI/元数据/CHANGELOG/Monorepo）→ 0.4.0 逻辑一致性修复（日期写死、触发词歧义、重复定义）→ 0.5.0 自检防幻觉边界 + 人类文档体系

## 9. 扩展与贡献指南

修改本技能时遵循以下约束：

1. **改动先过自检边界**：新增检查项必须进入 §5.4 的封闭清单本体，而不是运行时即兴发挥。
2. **保持跨平台命令纪律**：不引入 Unix 专有命令；新增平台时在 `agent-paths.md` 补路径表，在 README 安装表补目录。
3. **触发词变更须同步 test-prompts.json**：改触发语义时必须更新对应场景的 `verification_points` 和 `expected_output`。
4. **尺寸红线优先于功能**：SKILL.md 本身应保持可全量加载的体量；新增细节优先外移到 `references/`。
5. **CLAUDE.md / AGENTS.md 双名原则**：文档中提及规则手册时统一写"CLAUDE.md / AGENTS.md"（0.3.0 起的全局约定）。
