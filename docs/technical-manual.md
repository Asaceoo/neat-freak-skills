# neat-freak 技术手册

> 面向开发者和贡献者的内部机制说明：架构设计、流程引擎、确定性工具链与扩展指南。
> 使用层面的安装与操作见 [用户手册](user-guide.md)。

## 1. 设计哲学

neat-freak 的全部机制建立在四个设计判断上：

1. **代码可以随时重写，文档和记忆是跨会话、跨 Agent 的唯一桥梁**。记忆里的过期信息会让下一个 Agent 基于错误前提做决策——这是比"没有文档"更隐蔽的危害。
2. **三类知识、三种受众**。Agent 记忆（受众：Agent 自己）、CLAUDE.md / AGENTS.md（受众：项目内的 AI）、docs/ + README（受众：人类同事与下游开发者）。三层受众不同、职责不同，同步时必须分别处理，只改 CLAUDE.md 就结束是最常见的翻车模式。
3. **记忆只增不改、docs 就地编辑的不对称**。docs 靠就地编辑天然收敛；agent 记忆天生只追加，没有反向阀门必然膨胀到比 docs 还大。反向阀门就是"毕业"机制（§5.3）。
4. **CLAUDE.md / AGENTS.md 是规则手册，不是变更日志**。历史叙事进 git log / CHANGELOG；判断一条信息是否该进规则手册的标准是："下次 AI 写代码时如果没看到这条，会不会犯错？"

> 概念的完整论证（含判据、反例、平台对照）在 `skill/references/concepts.md`，Agent 首次执行本技能前必读；本手册不再重复。

## 2. 文件结构与组件职责

```
neat-freak-skills/
├── skill/                              # Skill 运行时文件（Agent 读取）
│   ├── SKILL.md                        # 主引擎：流程定义、原则、触发条件（~350 行 / ~30KB）
│   ├── references/                     # 按需加载的参考模块
│   │   ├── concepts.md                 # 概念层：三类知识 / 毕业机制 / 规则手册非日志的完整论证
│   │   ├── doc-standards.md            # 文档规范基线（CLAUDE.md 11 板块 / README 11 板块 / docs/ 规范）
│   │   ├── sync-matrix.md              # 变更影响矩阵（变更类型 → 应改文件 的完整映射表）
│   │   ├── agent-paths.md              # 各平台记忆与配置路径速查（Claude Code / Codex / WorkBuddy / OpenClaw / OpenCode）
│   │   └── init-report-template.md     # 初始化审查报告模板（含 15 项一致性检查表）
│   └── scripts/                        # 确定性辅助工具（纯标准库，见 §7）
│       ├── docs_lint.py                # 文档 lint：链接 / 相对时间 / TODO / 标题 / 记忆尺寸
│       └── regression_check.py         # 技能自身回归 harness：锚点 / 哨兵 / 引用链
├── docs/                               # 面向人类的文档（本目录）
├── test-prompts.json                   # 测试协议（3 场景 + expected_output 断言）
├── README.md / CHANGELOG.md / LICENSE  # 项目治理文件
```

**设计要点**：运行时文件（`skill/`）与治理文件（根目录）分层存放。SKILL.md 是核心文档，`references/` 是详细文档，两者已构成完整文档体系，因此 Skill 类项目**不强制建 docs/**（本仓库的 docs/ 服务于人类贡献者，不属于运行时依赖）。

**0.6.0 的分层重构**：SKILL.md 从 452 行瘦身到 350 行——概念论证迁入 `concepts.md`，15 项一致性检查表与操作清单示例迁入 `init-report-template.md`。依据是 Gloaguen（2026）对 138 个仓库的实证：上下文文件越长，agent 遵循度（adherence）越差。SKILL.md 保留的核心是"下一步做什么"（流程 + 规则 + 自检），而非"为什么"。

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

## 4. 硬停点（CHECKPOINT）编码

v0.5.1 起确认点以标记语法显式编码（`🔴 CHECKPOINT · 🛑 STOP`），替代"靠语义猜"的隐式停顿——Agent 执行时按标记硬停，不依赖对正文语气的解读。全文共 3 处：

| # | 位置 | 硬停条件 |
|---|------|----------|
| 1 | 初始化 Step 2-init | 审查报告获用户**明确确认**前，禁止执行任何文件修改 |
| 2 | 全局配置写入闸门 | 用户未明确表达跨项目核心原则时，`~/.claude/CLAUDE.md` / `~/.codex/AGENTS.md` 一律不写 |
| 3 | 记忆矛盾暂停 | 无法自动判断的矛盾硬停，列入「未处理」交用户裁决 |

`regression_check.py` 将"CHECKPOINT ≥ 3"列为回归哨兵——后续编辑若意外删除标记会被立即发现。

## 5. 流程引擎

### 5.1 初始化（Step 0-init ~ Step 4-init）

- **Step 0-init 代码事实提取**：以代码为唯一事实基准，提取 15 类事实（项目类型含 Skill 类识别、技术栈、目录结构、命令、环境变量、API/路由、数据模型、入口、测试、规范配置、依赖、协议、配置文件、CI/CD、元数据）。只记录实际存在的事实，不推断意图。
- **Step 1-init 一致性审查**：维度一为 15 项一致性比对（命令、环境变量、API、技术栈、配置、CI/CD、CHANGELOG 声明、代码逻辑 vs 架构文档、链接有效性等，详见 `init-report-template.md`）；维度二为按 doc-standards.md 板块清单的完整性标注。
- **Step 2-init 用户确认**：硬门槛（CHECKPOINT #1）。清单按 🔴 修复不一致 → 🟡 新建 → 修改 → 迁移排序；支持全部 / 部分 / 调整 / 取消。
- **Step 3-init 执行**：顺序为修复不一致 → docs/ → CLAUDE.md / AGENTS.md（只建一个）→ README.md → 迁移清理；每文件改后即校验。
- **Step 4-init 终检**：逐条终检 + 写入 `<!-- neat-freak: initialized at <当天日期> -->`（优先规则手册，否则 README）。红线：CLAUDE.md / AGENTS.md 和 README.md 至少存在一个。

### 5.2 常规同步（第零 ~ 五步）

- **第零步 尺寸体检（最高优先级）**：CLAUDE.md / AGENTS.md ~300 行（软）；MEMORY.md **≤200 行且 ≤25KB（硬，超限部分会话开始时静默不加载）**；单条记忆 ~100 行；docs 单文件 ~1500 行。另做**体量倒挂**体检：memory 总体积不应大于 docs 总体积。先精简后补漏，两件事不能合并做。
- **第一步 机械式枚举**：ls + Glob 兜底，逐文件读并标注"评估过 / 要改 / 不用改"。不依赖 Unix 专有命令（`wc -l` / `du` / `find`），保证 Windows 可用。
- **第二步 变更影响矩阵**：看"新事实波及哪些文档层级"而非对话增量；跨项目改动上下游两边 docs 都要改。完整映射查 `sync-matrix.md`。
- **第三步 编辑原则**：减优于加（CLAUDE.md 净涨幅 >30 行即红灯）→ 合并优于追加 → 删除优于保留 → 毕业优于内部挪腾 → 精确 + 绝对时间 → 受众不混 + 指针不重复。
- **第四步 自检清单（封闭式）**：尺寸/反膨胀组 + 完整性/反漏改组逐项核对。**自检边界**：清单封闭，禁止自创检查项后改文档再报"自检发现并修复"；清单外真实问题标 ⚠️ 列入未处理。文档与代码冲突且代码是错的，改代码不改文档。
- **第五步 变更摘要**：按"记忆 / 文档（按项目分组）/ 配置与 CI/CD / 未处理"输出，只列实际变更。

### 5.3 记忆写入规则（v0.6.0 升级）

| 规则 | 做法 | 来源 |
|------|------|------|
| **毕业机制** | 稳定/复用/本属"系统怎么工作"的记忆 → 并进 docs，原文件缩成一行指针。判据："下一个接手的人需要知道这件事吗？" | 原有 |
| **失效标记** | 被取代的记忆**不无痕删除**，缩成 `- superseded: YYYY-MM-DD → 已并入 <去处>`，保留审计线索 | Zep 双时间戳思路 |
| **时间戳** | 记忆文件 frontmatter 写 `created` / `updated: YYYY-MM-DD`，过期判断有据可依 | Claude Code Auto Memory |
| **Monorepo 冲突裁决** | 两份规则手册冲突时，**最近修改的文件优先** | AGENTS.md 规范 |

## 6. 平台适配层

neat-freak 本身零依赖，靠 Agent 自身工具能力（Read / Glob / Grep / Edit / Write）实现全部动作。平台差异集中在两处：

- **记忆系统位置**：由 `references/agent-paths.md` 速查表适配——Claude Code（`~/.claude/projects/<...>/memory/`）、Codex（无独立记忆，全写 AGENTS.md）、WorkBuddy（`<workspace>/.workbuddy/memory/`）、OpenClaw（`~/.openclaw/`）、OpenCode（扫描 Claude/Codex 目录）。当前 agent 没有独立记忆系统时跳过该层，docs 仍是最低保障。
- **跨平台命令**：SKILL.md 全程避免 `wc -l` / `du` / Unix `find`，改用 Read 工具 / Glob / `dir`，保证 Windows 会话可用。

## 7. 确定性工具链（skill/scripts/）

v0.6.0 新增。设计动机：SKILL.md 的一致性检查原本全靠 LLM 逐条比对，存在幻觉风险与不可复现性；docs-drift 检测器、Sphinx doctest 等成熟方案证明"链接、命令、锚点"类检查可以做成确定性脚本。工具链把**机器能查的交给机器**，LLM 只负责需要判断力的部分（语义一致性、受众适配）。

### 7.1 docs_lint.py — 文档 lint（告警级，不阻断）

```bash
python docs_lint.py <目标目录>   # 可指向任何项目或技能目录
```

| 检查项 | 说明 |
|--------|------|
| 相对链接有效性 | 剥离代码块/行内代码后提取 `[text](path)`，剥 `#fragment` 后查文件存在性 |
| 相对时间词 | 扫描 `今天/昨天/刚刚/最近/today/recently` 等，命中即告警 |
| TODO 占位符 | `TODO` / `FIXME` / `XXX` / `<占位>` |
| 标题层级跳跃 | `##` 直接跳 `####` 等 |
| MEMORY.md 尺寸红线 | ≤200 行且 ≤25KB（硬限制，对应静默截断阈值） |

已知良性告警：SKILL.md 规则文本里**引用**"今天/最近"等词本身会命中（如"不写'今天'"）——告警级设计即为此留了余地，人工复核后忽略即可。

### 7.2 regression_check.py — 技能回归 harness（阻断级）

```bash
python regression_check.py    # 无参数，扫描自身所在技能根目录
```

| 检查组 | 内容 |
|--------|------|
| 流程锚点 | 30 个关键标题/锚点必须存在（初始化 5 步、同步 6 步、自检、反例黑名单等） |
| 哨兵项 | 故意布置的探针必须被检出——验证检查器自身在工作，而非静默通过 |
| CHECKPOINT 计数 | `🔴 CHECKPOINT` ≥ 3（硬停点不可丢失） |
| frontmatter | SKILL.md 必填字段完整 |
| 引用链（双向） | SKILL.md 引用的 references 文件必须存在（防断裂）；references 目录里的文件必须被引用（防闲文件） |
| 测试协议 | test-prompts.json schema 完整 |

**工作流**：修改 SKILL.md 或 references 后跑一遍，输出 `ALL CHECKS PASSED` 即可发布；任何锚点丢失、引用断裂、标记缺失都会被逐条点名。

## 8. 测试协议（test-prompts.json）

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

可用于 dry_run 评估：把 `prompt + context` 喂给装好技能的 Agent，对照 `expected_output` 的 must_contain / must_not_contain 断言判定。三层验证互补：**regression_check.py（结构）→ test-prompts.json（行为）→ 鲁班类评估器（质量评分）**。

## 9. 版本与兼容性

- 当前版本：**0.6.0**（详见 [CHANGELOG](../CHANGELOG.md)）
- 兼容运行时：Claude Code · OpenAI Codex · OpenCode · OpenClaw · WorkBuddy
- 协议：MIT（见 [LICENSE](../LICENSE)）
- 版本演进主线：0.1.0 方法论奠基 → 0.2.0 内容外移 references/ → 0.3.0 审查维度扩充 → 0.4.0 逻辑一致性修复 → 0.5.0 自检防幻觉边界 + 人类文档体系 → 0.5.1 CHECKPOINT 硬停编码 → 0.5.2 反例黑名单独立章节 → 0.6.0 瘦身重构 + 确定性工具链 + superseded/时间戳规则

## 10. 扩展与贡献指南

修改本技能时遵循以下约束：

1. **改完先跑 `regression_check.py`**：锚点、CHECKPOINT 计数、双向引用链任一失败即回滚修正——这是 0.6.0 起的强制闭环。
2. **改动先过自检边界**：新增检查项必须进入封闭自检清单本体（SKILL.md §自检清单），而不是运行时即兴发挥。
3. **尺寸红线优先于功能**：SKILL.md 保持可全量加载的体量（目标 ≤300 行、硬顶 350）；新增细节优先外移到 `references/`；纯 Python 标准库可进 `scripts/`。
4. **保持跨平台命令纪律**：不引入 Unix 专有命令；新增平台时在 `agent-paths.md` 补路径表，在 README 安装表补目录。
5. **触发词变更须同步 test-prompts.json**：改触发语义时必须更新对应场景的 `verification_points` 和 `expected_output`。
6. **CLAUDE.md / AGENTS.md 双名原则**：文档中提及规则手册时统一写"CLAUDE.md / AGENTS.md"（0.3.0 起的全局约定）。
7. **反例黑名单同步**：新增反模式时同时更新 SKILL.md「反例黑名单」章节（❌ 反模式 → ✅ 替代做法 结构）。
