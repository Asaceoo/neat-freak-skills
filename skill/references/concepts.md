# 核心概念详解 — 为什么 neat-freak 这样设计

> 本文件是 SKILL.md「核心概念速览」的完整版。首次执行本技能前通读一遍；熟练后速览即可。
> 依据：Gloaguen et al. (2026) 对 138 个真实仓库的实证研究——上下文文件越长，agent adherence 越差。概念解释属于"读一次就懂"的内容，不应常驻主流程文件。

## 为什么这件事重要

在 AI 协作开发中，代码可以随时重写，但**文档和记忆是跨会话、跨 Agent 的唯一桥梁**。如果记忆里有过期信息，下一个 Agent（无论它是 Claude、Codex 还是别的）会基于错误前提做决策。如果 docs/ 混乱或缺失，接手者（尤其是下游项目的同事）会浪费大量时间搞清楚这套系统怎么用。

这个 Skill 的价值就在于：**让知识体系的每一层都跟得上代码的变化。**

## 三类知识，三种受众

| 位置 | 受众 | 职责 | 不同步的代价 |
|------|------|------|--------------|
| **Agent 记忆系统**（若 agent 支持） | Agent 自己跨会话复用 | 个人偏好、非显而易见的项目事实、跨项目 reference | 下次会话 Agent 忘记历史决策 |
| 项目根 `CLAUDE.md` / `AGENTS.md` | 当前项目里的 AI（下次会话自己） | 项目约定、结构、红线、环境变量、路由清单 | 下次 AI 在这个项目里走弯路 |
| 项目 `docs/` + `README.md` | **其他人**（人类同事、下游开发者、未来接手的 AI） | 接入指南、架构图、运维手册、交接说明、API 参考 | **其他人或系统无法正确接入或运维** |

### CLAUDE.md / AGENTS.md vs README.md：受众不同，职责不同

**CLAUDE.md / AGENTS.md 告诉 AI "你应该怎么做事"**——就像给一位聪明但完全不了解项目背景的 AI 新同事写的"入职手册 + 行为准则"，用具体、可执行的语言，把"项目是什么、怎么跑、怎么写代码、绝对不能做什么"一次性说清楚。

**README.md 告诉人类 "这个项目能做什么"**——优秀的 README 是对读者时间的尊重，用最短的时间让人说"我懂了，这有用"，并给出清晰的下一步。始终站在新手的视角，让它能复制、能运行、能看懂。

两者**受众不同、内容不重叠**。CLAUDE.md 里写"Prisma 查询只写在 `modules/**/data/`" ≠ README 里写"快速开始：npm install && npm run dev"——前者是告诉 AI 行为约束，后者是告诉人怎么用。**两份都要有，不能互相替代。**

> **CLAUDE.md 和 AGENTS.md 功能等价，只维护一个即可。** 如果项目同时被多个 agent 平台使用，一份主文件 + 另一份用一行 `See CLAUDE.md` 跳转。同时维护两份只会导致信息不一致。

> **Agent 记忆系统的具体位置因平台而异**（Claude Code 在 `~/.claude/projects/<...>/memory/`，Codex 用 `AGENTS.md`，OpenCode 用 `.opencode/`，OpenClaw 用 `~/.openclaw/`）。完整路径速查见 [agent-paths.md](agent-paths.md)。如果当前 agent 没有独立的记忆系统，直接跳过这一层，把功夫全花在 docs 和项目根 markdown 上。

## 记忆只增不改、docs 就地编辑——要靠「毕业」机制把知识往上泵（膨胀头号根因）

必须理解这条不对称，否则记忆永远在膨胀：**docs 靠就地编辑收敛**（系统改 10 次，还是那一份 `ARCHITECTURE.md`），**而 agent 记忆天生只追加**（每条教训生一个新文件，旧的不删）。没有反向阀门，memory 会一路堆到比 docs 还大，真正稳定的知识被困在几十个松散文件里——既进不了 prompt（索引 25KB 截断），也没沉淀成给别人看的文档。高速开发的项目尤其明显：每天 2-3 条教训 × 数周 = 上百个记忆文件。

**反向阀门 = 毕业（promote）。** 一条记忆满足下面任一条，就把它「毕业」：内容并进对应的 `docs/` 或 CLAUDE.md / AGENTS.md，然后**把原记忆文件缩成一行失效指针或删除**：

- **同一主题的教训反复出现到第 3 次** → 它已是稳定知识而非「最近踩的坑」，归 docs。
- **它讲的是「系统怎么工作」而非「我们踩过什么坑 / 做过什么决策」** → 本就是 docs 的职责，memory 顶多留指针。
- **它是「X 上线 / 落地 / 就位」的事件记录** → 现役事实进 docs，过程进 git log / `docs/CHANGES.md`，memory 不留常驻文件。

**失效指针优于物理删除（借鉴 Zep 双时间戳思路）**：被新版本取代的记忆缩成一行 `- superseded: YYYY-MM-DD → 已并入 docs/X.md §Y`，保留审计回溯能力——误删不可恢复，失效标记可以。物理删除仅用于无审计价值的临时计划、流水账。判据一句话：**「下一个接手的人（不只是我自己）需要知道这件事吗？」需要 → 它属于 docs，不是 memory。**

> 记忆文件若用类型前缀（如 `feedback_`=教训 / `project_`=决策事件 / `reference_`=速查），生命周期不同：`reference_` 通常合法长期常驻；`feedback_` 稳定后毕业；`project_` 多数是事件记录，**是优先毕业 / 删除的对象**——决策结论进 docs，过程进 changelog。

**记忆条目带时间戳（借鉴 Claude Code `modified` frontmatter）**：新建 / 更新记忆文件时在 frontmatter 写 `updated: YYYY-MM-DD`（`created` 首次创建时写一次并保留），供尺寸体检与过期审查时量化判断"这条记忆多老了"。

## CLAUDE.md / AGENTS.md 是规则手册，不是变更日志（重要）

最常见的 skill 翻车模式：每次开发完都在 CLAUDE.md / AGENTS.md 顶部加一段 blockquote 历史叙事——"2026-05-08 X 功能上线，详见 docs/Y.md"。一次很爽，半年后顶部就是 200 行 blockquote 把真正的规则推到看不见。**这种叙事不属于 CLAUDE.md / AGENTS.md**，它的归宿是 git log / `/changelog` 页 / `docs/CHANGES.md`。

判断一条信息该不该进 CLAUDE.md / AGENTS.md，问一句：**下次 AI 写代码时如果没看到这条，会不会犯错？**

| 例子 | 进 CLAUDE.md / AGENTS.md？ | 理由 |
|---|---|---|
| "Prisma 查询只写在 `modules/**/data/`" | ✅ | 违反就是边界破坏，AI 必须看到 |
| "rsync 单文件部署必须用完整 target 路径" | ✅ | 踩坑警示，会再次踩 |
| "禁止裸跑 systemctl stop aihot-worker" | ✅ | 红线，事故级 |
| "2026-05-08 timelineAt 上线，详见 docs/ARCHITECTURE.md §5.4" | ❌ | 详细机制在 docs；AI 改到这块自然会读 docs；「深入文档」指针表已做这件事 |
| "2026-04-30 起公网开放，匿名可访 /、/all" | ❌ | 既是历史也是事实，但事实归 docs/ARCHITECTURE.md §8 + 项目概览一句话足矣 |
| "5/8 修了 X bug 的复盘细节" | ❌ | 单次事故记忆，归 memory 或干脆删 |

✅ 该进 CLAUDE.md / AGENTS.md 的内容：硬边界规则、禁止事项、命令速查、权限模型、协作流程、深入文档指针表、踩坑警示。
❌ 不该进的：历史叙事（"X 时刻起 Y 上线"）、详细机制说明、单次事故复盘、bug fix 流水账、"详见 docs/Z.md" 的指针句子（这个角色已经被「深入文档」指针表占掉了）。
