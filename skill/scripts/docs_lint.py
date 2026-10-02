#!/usr/bin/env python3
"""
docs_lint.py — neat-freak 确定性文档 lint（O2：把可机械化的自检项做成脚本）。

检查项（全部确定性，无 LLM 参与）：
  1. 相对链接有效性（剥离代码块/行内代码与 #fragment 后检查文件存在性）
  2. 相对时间词扫描（今天/昨天/刚刚/最近/上周/today/yesterday/recently）— 告警级
  3. TODO / FIXME / XXX 占位符扫描 — 告警级
  4. 标题层级跳跃检查（h1→h3 等）— 告警级
  5. MEMORY.md 尺寸红线（≤200 行且 ≤25KB，超限为错误）

用法: python docs_lint.py <project_dir> [--json]
退出码: 0 = 无错误（告警不算）；1 = 有错误
"""
import argparse
import json
import re
import sys
from pathlib import Path

RELATIVE_TIME = re.compile(
    r"(今天|昨天|刚刚|最近|上周|今天|today|yesterday|recently)", re.IGNORECASE
)
TODO_RE = re.compile(r"\b(TODO|FIXME|XXX)\b")
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^\)]+)\)")
HEADING_RE = re.compile(r"^(#{1,6})\s")


def strip_code(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"~~~.*?~~~", "", text, flags=re.DOTALL)
    text = re.sub(r"`[^`\n]*`", "", text)
    return text


def iter_markdown(root: Path):
    skip_dirs = {"node_modules", ".git", ".venv", "venv", "__pycache__", "dist", "build"}
    for p in sorted(root.rglob("*.md")):
        if any(part in skip_dirs for part in p.parts):
            continue
        yield p


def check_links(root: Path, files) -> list:
    issues = []
    for p in files:
        try:
            text = strip_code(p.read_text(encoding="utf-8"))
        except Exception as e:
            issues.append({"file": str(p), "severity": "error", "check": "readable",
                           "issue": f"无法读取: {e}"})
            continue
        base = p.parent
        for link_text, url in LINK_RE.findall(text):
            if url.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path_part = url.split("#", 1)[0]
            if not path_part:
                continue
            if not (base / path_part).exists():
                issues.append({"file": str(p), "severity": "error", "check": "link",
                               "issue": f"断裂: [{link_text}]({url})"})
    return issues


def check_patterns(root: Path, files) -> list:
    issues = []
    for p in files:
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines, 1):
            m = RELATIVE_TIME.search(line)
            if m:
                issues.append({"file": str(p), "severity": "warning", "check": "relative-time",
                               "line": i, "issue": f"相对时间词「{m.group(1)}」: {line.strip()[:60]}"})
            m = TODO_RE.search(line)
            if m:
                issues.append({"file": str(p), "severity": "warning", "check": "todo",
                               "line": i, "issue": f"占位符 {m.group(1)}: {line.strip()[:60]}"})
    return issues


def check_headings(root: Path, files) -> list:
    issues = []
    for p in files:
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        prev = 0
        for i, line in enumerate(lines, 1):
            m = HEADING_RE.match(line)
            if m:
                level = len(m.group(1))
                if prev and level > prev + 1:
                    issues.append({"file": str(p), "severity": "warning", "check": "heading",
                                   "line": i, "issue": f"标题层级跳跃 h{prev}→h{level}: {line.strip()[:50]}"})
                prev = level
    return issues


def check_memory_index(root: Path) -> list:
    issues = []
    for name in ("MEMORY.md", "memory/MEMORY.md"):
        f = root / name
        if not f.exists():
            continue
        data = f.read_bytes()
        n_lines = data.count(b"\n") + 1
        if n_lines > 200:
            issues.append({"file": str(f), "severity": "error", "check": "memory-size",
                           "issue": f"MEMORY.md {n_lines} 行 > 200 行硬上限（超出部分静默不加载）"})
        if len(data) > 25 * 1024:
            issues.append({"file": str(f), "severity": "error", "check": "memory-size",
                           "issue": f"MEMORY.md {len(data)} 字节 > 25KB 硬上限（超出部分静默不加载）"})
    return issues


def main():
    ap = argparse.ArgumentParser(description="neat-freak 确定性文档 lint")
    ap.add_argument("project_dir", help="目标项目/技能目录")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    root = Path(args.project_dir).resolve()
    if not root.exists():
        print(json.dumps({"error": f"目录不存在: {root}"}, ensure_ascii=False))
        sys.exit(1)

    files = list(iter_markdown(root))
    issues = (check_links(root, files) + check_memory_index(root)
              + check_patterns(root, files) + check_headings(root, files))
    errors = [i for i in issues if i["severity"] == "error"]
    warnings = [i for i in issues if i["severity"] == "warning"]

    report = {
        "project_dir": str(root),
        "files_scanned": len(files),
        "errors": len(errors),
        "warnings": len(warnings),
        "issues": issues,
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"扫描 {len(files)} 个 markdown 文件: {len(errors)} 错误 / {len(warnings)} 告警")
        for i in issues:
            loc = f"{i.get('line', '')}" 
            print(f"  [{i['severity']}] {i['check']} {Path(i['file']).name}:{loc} — {i['issue']}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
