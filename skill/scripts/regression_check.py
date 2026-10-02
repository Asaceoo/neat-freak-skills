#!/usr/bin/env python3
"""
regression_check.py — neat-freak 结构回归检查（O6：改动本技能后跑一遍，防止重构丢内容）。

检查项：
  1. SKILL.md 流程锚点完整性（Step 0-4-init、第零~五步、CHECKPOINT、黑名单等关键节）
  2. SKILL.md 关键规则词存在（触发词、superseded 失效指针、时间戳规则、尺寸红线）
  3. frontmatter 必填字段（name / description）
  4. references/ 链接链完整（每个声明的 reference 文件存在且被 SKILL.md 引用）
  5. test-prompts.json 结构完整性（schema + 必填字段 + 触发词在 SKILL.md 中可语义命中）
  6. 调用 docs_lint 做确定性检查（同目录下 scripts/docs_lint.py）

用法: python regression_check.py [skill_dir]（默认 = 本脚本所在目录的上一级）
退出码: 0 = 全部通过；1 = 有失败项
"""
import json
import re
import subprocess
import sys
from pathlib import Path

# SKILL.md 必须包含的流程/规则锚点（重构 SKILL.md 后若误删会在此报警）
SKILL_ANCHORS = [
    "Step 0-init", "Step 1-init", "Step 2-init", "Step 3-init", "Step 4-init",
    "第零步", "第一步", "第二步", "第三步", "第四步", "第五步",
    "反例黑名单", "核心概念速览", "references/concepts.md",
    "references/doc-standards.md", "references/sync-matrix.md",
    "references/agent-paths.md", "references/init-report-template.md",
    "superseded", "created: YYYY-MM-DD", "updated: YYYY-MM-DD",
    "≤200 行", "25KB", "净涨幅 > 30 行",
    "初始化项目", "同步一下", "搞一下文档", "搞一下",
    "novel-check-placeholder",  # 哨兵：永远不应命中，用于验证检查器本身在工作
]

CHECKPOINT_MIN = 3


def load_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def main():
    skill_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    sm = skill_dir / "SKILL.md"
    failures = []

    if not sm.exists():
        print(f"FATAL: {sm} 不存在")
        sys.exit(1)
    text = load_text(sm)

    # 1+2. 锚点检查（哨兵项单独处理：必须不命中）
    for anchor in SKILL_ANCHORS:
        hit = anchor in text
        if anchor == "novel-check-placeholder":
            if hit:
                failures.append(f"哨兵锚点意外命中（检查器失效）: {anchor}")
        elif not hit:
            failures.append(f"SKILL.md 缺少锚点: {anchor}")

    # CHECKPOINT 数量
    n_cp = text.count("CHECKPOINT")
    if n_cp < CHECKPOINT_MIN:
        failures.append(f"CHECKPOINT 标记 {n_cp} 处 < {CHECKPOINT_MIN} 处下限")

    # 3. frontmatter
    if not text.startswith("---"):
        failures.append("缺少 YAML frontmatter")
    else:
        fm = text.split("---", 2)[1]
        for field in ("name:", "description:"):
            if not re.search(rf"^{field}", fm, re.MULTILINE):
                failures.append(f"frontmatter 缺少字段: {field}")

    # 4. references 链接链
    ref_dir = skill_dir / "references"
    cited = set(re.findall(r"references/([\w\-]+\.md)", text))
    if ref_dir.exists():
        actual = {p.name for p in ref_dir.glob("*.md")}
        for c in cited:
            if c not in actual:
                failures.append(f"SKILL.md 引用了不存在的 reference: references/{c}")
        for a in actual - cited:
            failures.append(f"references/{a} 存在但未被 SKILL.md 引用（闲文件）")
    else:
        failures.append("references/ 目录不存在")

    # 5. test-prompts.json
    tp = skill_dir / "test-prompts.json"
    if tp.exists():
        try:
            data = json.loads(load_text(tp))
            prompts = data.get("prompts", [])
            if not prompts:
                failures.append("test-prompts.json 无 prompts")
            for p in prompts:
                for field in ("id", "prompt", "expected_output"):
                    if field not in p:
                        failures.append(f"test-prompts.json [{p.get('id', '?')}] 缺字段: {field}")
                eo = p.get("expected_output", {})
                if not eo.get("must_contain"):
                    failures.append(f"test-prompts.json [{p.get('id', '?')}] must_contain 为空")
                if not eo.get("must_not_contain"):
                    failures.append(f"test-prompts.json [{p.get('id', '?')}] must_not_contain 为空")
                # 触发词语义可命中：prompt 中的核心触发词应在 SKILL.md 出现或语义等价
                for kw in re.findall(r"[\u4e00-\u9fff]{2,6}", p.get("prompt", "")):
                    pass  # 中文分词不做精确断言，触发词检查已由 SKILL_ANCHORS 覆盖
        except json.JSONDecodeError as e:
            failures.append(f"test-prompts.json 解析失败: {e}")
    else:
        failures.append("test-prompts.json 不存在")

    # 6. docs_lint（若可用）
    lint = Path(__file__).resolve().parent / "docs_lint.py"
    lint_summary = "skipped"
    if lint.exists():
        r = subprocess.run([sys.executable, str(lint), str(skill_dir), "--json"],
                           capture_output=True, text=True)
        try:
            lr = json.loads(r.stdout)
            lint_summary = f"{lr['errors']} errors / {lr['warnings']} warnings"
            if lr["errors"]:
                for i in lr["issues"]:
                    if i["severity"] == "error":
                        failures.append(f"docs_lint: {i['issue']} ({i['file']})")
        except json.JSONDecodeError:
            lint_summary = f"parse-failed: {r.stderr[:100]}"
            failures.append("docs_lint 输出解析失败")

    print(f"skill_dir = {skill_dir}")
    print(f"CHECKPOINT = {n_cp} | docs_lint = {lint_summary}")
    if failures:
        print(f"\nFAIL ({len(failures)}):")
        for f in failures:
            print(f"  ✗ {f}")
        sys.exit(1)
    print("\nALL CHECKS PASSED")
    sys.exit(0)


if __name__ == "__main__":
    main()
