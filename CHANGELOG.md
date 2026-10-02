# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-10-02

### Added
- 新增 `docs/user-guide.md` 用户手册：安装（含 WorkBuddy 路径）、语义触发方式、初始化/常规同步两种模式的使用体验、交付物解读、安全边界、FAQ
- 新增 `docs/technical-manual.md` 技术手册：设计哲学、文件结构与组件职责、模式判定引擎、初始化/常规同步流程引擎内部机制、毕业机制与尺寸红线、测试协议、扩展与贡献指南
- README 新增「文档」章节，文件结构图补充 docs/ 目录，安装命令更新为实际仓库地址，补充 WorkBuddy 安装路径

### Fixed
- SKILL.md 第四步自检清单后新增「自检边界」原则：自检清单是封闭的，禁止自创检查项后自行修改文档（防止幻觉性自检越权）。触发场景：GLM-5V-Turbo 在自检阶段虚构"评分表总分 100→105"问题并直接修改文档，未报告用户。修复方式：明确自检范围封闭、清单外真实问题按「代码 bug」流程标注 ⚠️ 列入未处理、禁止"自检发现并修复"式越权

## [0.4.0] - 2026-06-21

### Added
- README 首屏升级：排他式定位（"文档漂移的审计员 — 不存记忆、不做检索，只做一件事"）+ 可量化卖点（14 项自检清单 / 三层知识分层 / 毕业机制）
- README 安装说明升级：支持命令行安装（git clone + cp）和手动复制两种方式，按 runtime 给具体路径（Claude Code / Codex / OpenClaw / OpenCode）
- README 新增「示例」章节：3 个场景的文本块示例输出（初始化审查报告 / 常规同步变更摘要 / 记忆毕业前后对比）
- test-prompts.json 升级：每个场景新增 `expected_output` 字段（含 stage / must_contain / must_not_contain / example_fragment），可用于 dry_run 评估

### Changed
- SKILL.md L238 修复日期写死：`<!-- neat-freak: initialized at 2026-06-16 -->` → `<!-- neat-freak: initialized at <执行当天日期 YYYY-MM-DD> -->`（防止 Agent 照抄示例日期）
- SKILL.md L318 修复日期示例：`永远 2026-04-29` → `永远用绝对日期 YYYY-MM-DD（如 2026-04-29）`（防止 Agent 误以为每次都要写这个日期）
- SKILL.md L397 修复"vibe 阶段"模糊词：改为可判断的条件"项目根目录是否有可执行入口文件（package.json / go.mod / pyproject.toml / Cargo.toml / src/ 等任一存在）"
- SKILL.md L96 修复触发词歧义："搞一下文档" / "搞一下" 从初始化触发词移至常规同步触发词（用户确认：输入"搞一下文档"按同步计算，不按初始化）
- SKILL.md L126 合并重复定义：Skill 类项目目录结构检查不再重复描述分层规则，改为引用"项目类型"中定义的分层规则

### Fixed
- 逻辑一致性扫描发现的 4 个问题（见上 Changed）：日期写死、日期示例、模糊词、重复定义

### 鲁班打磨报告
- 完整打磨报告见 `luban-report-neat-freak-20260621.md`（含验料/访行/过尺/差距清单/三个方向/回炉清单）

## [0.3.0] - 2026-06-20

### Added
- Step 0-init 新增 3 项代码事实提取：配置文件内容、CI/CD 配置、项目元数据
- Step 0-init 新增「代码逻辑与设计文档一致性提取」（数据流/模块调用/状态机偏差）
- Step 1-init 一致性检查表新增 6 项：配置文件一致性、CI/CD 与文档对齐、项目元数据一致性、CHANGELOG 与代码一致性、代码逻辑与设计文档一致性、文档内链接有效性
- 常规同步第一步新增 4 项盘点动作：配置文件、CI/CD 配置、项目元数据、CHANGELOG 最近 20 行
- 常规同步第二步常见模式速览新增 4 项：配置文件变更、CI/CD 配置变更、项目元数据变更、代码逻辑/架构偏差修正
- 常规同步第四步自检清单新增 6 项：文档内链接有效性、配置文件、CI/CD、元数据、CHANGELOG、代码逻辑
- 常规同步第五步变更摘要新增「配置与 CI/CD 变更」类别
- 特殊情况新增 Monorepo 场景处理规则（识别/文档层级/一致性专项/CHANGELOG 策略/同步规则）
- init-report-template.md 新增 6 个审查板块示例（配置文件/CI-CD/元数据/CHANGELOG/链接有效性/代码逻辑）
- doc-standards.md 新增 Monorepo 项目文档规范（目录结构/分层原则/6 条审查要点）
- sync-matrix.md 新增初始化映射 4 行 + 代码变更映射 5 行 + Monorepo 跨项目检查 2 条

### Changed
- 全文 ~25+ 处单独提及 CLAUDE.md 统一为 CLAUDE.md / AGENTS.md（5 个文件）
- 常规同步第四步跨平台命令修复：`wc -c` → Read 工具/dir；`du` → Glob+Read/dir /s
- sync-matrix.md 反向删除板块标题和内容统一为 CLAUDE.md / AGENTS.md

## [0.2.0] - 2026-06-20

### Added
- README.md — 项目首屏、快速开始、触发方式、安全边界、与同类对比
- LICENSE — MIT 协议
- test-prompts.json — 3 个典型测试场景（初始化/同步/语义触发）
- references/doc-standards.md — 从 SKILL.md 外移的文档规范基线
- 失败模式：审查后发现代码本身有 bug 的处理路径

### Changed
- SKILL.md description 从 ~20 行精简到 6 行，触发词列表移到正文
- SKILL.md 文档规范基线外移到 references/doc-standards.md，正文改为引用
- SKILL.md 跨平台命令修复（wc -l / find / grep -E → Read / Glob / Grep）
- SKILL.md 触发逻辑增加三级优先级（用户显式意图 > 自动检测 > 辅助信号）
- SKILL.md 初始化标记写入逻辑增加审查红线（CLAUDE.md/README.md 至少存在一个）
- sync-matrix.md 文档命名与 SKILL.md 规范基线对齐，补充扩展文档类型

### Removed
- neat-freak-person.zip（打包产物，不应纳入版本控制）

## [0.1.0] - 2026-06-15

### Added
- 初始版本：会话后知识库审查与同步方法论
- 初始化流程（5 步）和常规同步流程（6 步）
- 三类知识三种受众的分层框架
- "毕业"机制（memory → docs 的知识提升）
- 反膨胀体检（MEMORY.md ≤ 25KB / 200 行）
- references/sync-matrix.md — 变更影响矩阵
- references/agent-paths.md — 各 Agent 记忆路径速查
- references/init-report-template.md — 初始化审查报告模板
