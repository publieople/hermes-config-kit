#!/usr/bin/env python3
"""Skills + MEMORY.md 自动维护脚本
在每个 cron 任务执行前运行，输出注入到 prompt 作为维护上下文。

安全原则：
- 绝不自动删除用户数据 (只归档/报告)
- 所有修改前先备份
- 操作可逆
"""

import os
import re
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict

HERMES_HOME = Path.home() / ".hermes"
SKILLS_DIR = HERMES_HOME / "skills"
MEMORIES_DIR = HERMES_HOME / "memories"
BACKUP_DIR = MEMORIES_DIR / "backups"
ARCHIVE_DIR = SKILLS_DIR / "_archive"

MEMORY_FILE = MEMORIES_DIR / "MEMORY.md"
USER_FILE = MEMORIES_DIR / "USER.md"
MEMORY_CHAR_LIMIT = 2200
USER_CHAR_LIMIT = 1375
SKILL_WARN_LIMIT = 50       # 建议上限
SKILL_ARCHIVE_DAYS = 60     # 60 天未修改 → 归档候选
MEMORY_WARN_SIZE = 6000     # 6KB 警告线

now = datetime.now(timezone.utc)
report = {
    "timestamp": now.isoformat(),
    "memory": {},
    "skills": {},
    "actions_taken": [],
    "warnings": [],
    "recommendations": [],
}


# ═══════════════════════════════
# MEMORY.md 维护
# ═══════════════════════════════

def maintain_memory():
    mem_report = {}
    
    # 1. 检查文件是否存在
    if not MEMORY_FILE.exists():
        report["warnings"].append("MEMORY.md 不存在")
        write_empty = input("MEMORY.md not found. Create empty? [Y/n]: ")
        if write_empty.lower() != 'n':
            MEMORY_FILE.write_text("")
            report["actions_taken"].append("创建空白 MEMORY.md")
        return
    
    content = MEMORY_FILE.read_text(encoding="utf-8")
    size = len(content.encode("utf-8"))
    char_count = len(content)
    
    mem_report["size_bytes"] = size
    mem_report["char_count"] = char_count
    mem_report["char_limit"] = MEMORY_CHAR_LIMIT
    mem_report["usage_pct"] = round(char_count / MEMORY_CHAR_LIMIT * 100, 1)
    
    # 2. 检查是否超过限制
    if size > MEMORY_WARN_SIZE:
        report["warnings"].append(f"MEMORY.md 大小 {size} bytes，超过 {MEMORY_WARN_SIZE} 警告线")
    if char_count > MEMORY_CHAR_LIMIT:
        report["warnings"].append(
            f"MEMORY.md 字符数 {char_count} 超过限制 {MEMORY_CHAR_LIMIT}！"
            f"超出 {char_count - MEMORY_CHAR_LIMIT} 字符"
        )
    
    # 3. 备份（每天只保留最新备份，不堆积）
    backup_path = BACKUP_DIR / f"MEMORY.md.{now.strftime('%Y%m%d')}"
    if not backup_path.exists():
        shutil.copy2(MEMORY_FILE, backup_path)
        report["actions_taken"].append(f"MEMORY.md 已备份至 {backup_path}")
        # 清理 7 天前的旧备份
        for old_backup in sorted(BACKUP_DIR.glob("MEMORY.md.*"))[:-7]:
            old_backup.unlink()
            report["actions_taken"].append(f"清理旧备份: {old_backup.name}")
    
    # 4. 统计条目
    entries = [line for line in content.split("\n") if line.strip() and not line.strip().startswith(">")]
    # 提取记忆条目 (格式: "- 内容" 或 "§" 分隔的段落)
    entry_lines = [e.strip() for e in content.split("\n") if e.strip().startswith("- ")]
    section_entries = [s.strip() for s in content.split("§") if s.strip()]
    
    mem_report["total_lines"] = len(content.split("\n"))
    mem_report["entry_count"] = len(entry_lines)
    mem_report["section_count"] = len(section_entries)
    
    # 5. 去重（保留首次出现）
    lines = content.split("\n")
    seen = set()
    deduped = []
    dupes_found = 0
    for line in lines:
        stripped = line.strip()
        if stripped and stripped in seen:
            dupes_found += 1
            continue
        if stripped:
            seen.add(stripped)
        deduped.append(line)
    
    if dupes_found > 0:
        MEMORY_FILE.write_text("\n".join(deduped), encoding="utf-8")
        report["actions_taken"].append(f"MEMORY.md 去重: 移除 {dupes_found} 条重复项")
        report["warnings"].append(f"MEMORY.md 发现 {dupes_found} 条重复项，已自动清理")
        # 更新字符数
        new_content = "\n".join(deduped)
        mem_report["after_dedup_chars"] = len(new_content)
    
    # 6. 检查字数超出时的优化建议
    if char_count > MEMORY_CHAR_LIMIT * 0.9:
        # 看哪些条目可能是旧的（简单启发：检查有没有日期标记）
        old_pattern = re.compile(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}")
        dated_entries = [(line, line) for line in entry_lines if old_pattern.search(line)]
        if dated_entries:
            report["recommendations"].append(
                f"MEMORY.md 接近限制 ({mem_report['usage_pct']}%)。"
                f"以下条目包含日期标记，可考虑归档或精简：\n" +
                "\n".join(f"  - {e[:80]}" for _, e in dated_entries[:5])
            )
    
    # 7. USER.md 同样检查
    if USER_FILE.exists():
        user_content = USER_FILE.read_text(encoding="utf-8")
        user_chars = len(user_content)
        mem_report["user_chars"] = user_chars
        mem_report["user_limit"] = USER_CHAR_LIMIT
        mem_report["user_usage_pct"] = round(user_chars / USER_CHAR_LIMIT * 100, 1)
        if user_chars > USER_CHAR_LIMIT * 0.9:
            report["warnings"].append(f"USER.md 字符数 {user_chars} 接近限制 {USER_CHAR_LIMIT}")
    else:
        mem_report["user_exists"] = False
    
    report["memory"] = mem_report


# ═══════════════════════════════
# Skills 维护
# ═══════════════════════════════

def scan_skill_descriptions(skill_dir):
    """扫描一个 skill 的 description（从 SKILL.md 的 frontmatter 提取）"""
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.exists():
        return None
    
    content = skill_file.read_text(encoding="utf-8", errors="ignore")
    
    # 提取 frontmatter
    fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not fm_match:
        return {"name": skill_dir.name, "description": "", "triggers": []}
    
    fm = fm_match.group(1)
    
    # 提取 description
    desc_match = re.search(r"^description:\s*(.+)$", fm, re.MULTILINE)
    description = desc_match.group(1).strip() if desc_match else ""
    
    # 提取 triggers
    triggers = []
    in_triggers = False
    for line in fm.split("\n"):
        stripped = line.strip()
        if stripped == "triggers:" or stripped.startswith("triggers: "):
            in_triggers = True
            continue
        if in_triggers:
            if stripped.startswith("- "):
                triggers.append(stripped[2:].strip())
            elif not stripped.startswith("  - ") and not stripped.startswith("-"):
                in_triggers = False
    
    # 提取 tags
    tags = []
    in_tags = False
    for line in fm.split("\n"):
        stripped = line.strip()
        if stripped == "tags:" or stripped.startswith("tags: "):
            in_tags = True
            continue
        if in_tags:
            if stripped.startswith("- "):
                tags.append(stripped[2:].strip())
            elif not stripped.startswith("  - ") and not stripped.startswith("-"):
                in_tags = False
    
    return {
        "name": skill_dir.name,
        "description": description,
        "triggers": triggers,
        "tags": tags,
    }


def find_all_skills(base_dir):
    """递归查找所有 user-created SKILL.md 文件"""
    results = []
    exclude = {"hermes", "mcp", "_archive"}
    for root, dirs, files in os.walk(base_dir):
        root_path = Path(root)
        rel = root_path.relative_to(base_dir)
        parts = set(rel.parts) if rel != Path(".") else set()
        if parts & exclude:
            continue
        if ".git" in parts:  # 排除 git 内部
            continue
        if "SKILL.md" in files:
            skill_file = root_path / "SKILL.md"
            mtime = datetime.fromtimestamp(skill_file.stat().st_mtime, tz=timezone.utc)
            results.append((str(rel), mtime))
    return results


def maintain_skills():
    skills_report = {}
    
    # 统计所有 user-created skills (递归)
    user_skills = find_all_skills(SKILLS_DIR)
    
    total_count = len(user_skills)
    skills_report["total_count"] = total_count
    skills_report["warn_limit"] = SKILL_WARN_LIMIT
    
    if total_count > SKILL_WARN_LIMIT:
        report["warnings"].append(
            f"Skills 数量 {total_count} 超过建议上限 {SKILL_WARN_LIMIT}，超出 {total_count - SKILL_WARN_LIMIT} 个"
        )
    
    # 检查归档候选（60天未修改）
    archive_candidates = []
    for name, mtime in user_skills:
        age_days = (now - mtime).days
        if age_days >= SKILL_ARCHIVE_DAYS:
            archive_candidates.append((name, age_days, mtime))
    
    skills_report["archive_candidates"] = len(archive_candidates)
    if archive_candidates:
        report["recommendations"].append(
            f"以下 {len(archive_candidates)} 个 Skill 超过 {SKILL_ARCHIVE_DAYS} 天未修改：\n" +
            "\n".join(f"  - {name}（{days} 天，最后修改 {mtime.strftime('%m-%d')}）" for name, days, mtime in archive_candidates[:10])
        )
        if len(archive_candidates) > 10:
            report["recommendations"][-1] += f"\n  ... 及其他 {len(archive_candidates) - 10} 个"
    
    # 扫描 description 检测潜在重复
    skill_infos = []
    for skill_rel, _mtime in user_skills:
        skill_dir = SKILLS_DIR / skill_rel
        info = scan_skill_descriptions(skill_dir)
        if info and info["description"]:
            skill_infos.append(info)
    
    # 简单关键词相似度检测
    overlaps = []
    for i, si in enumerate(skill_infos):
        for sj in skill_infos[i+1:]:
            # 取 description 和 triggers 的关键词
            keywords_i = set(re.findall(r'\w+', si["description"].lower() + " " + " ".join(si["triggers"]).lower()))
            keywords_j = set(re.findall(r'\w+', sj["description"].lower() + " " + " ".join(sj["triggers"]).lower()))
            
            if not keywords_i or not keywords_j:
                continue
            
            common = keywords_i & keywords_j
            if len(common) >= 3:
                union = keywords_i | keywords_j
                overlap_ratio = len(common) / len(union) if union else 0
                
                if overlap_ratio >= 0.5:
                    overlaps.append({
                        "a": si["name"],
                        "b": sj["name"],
                        "ratio": round(overlap_ratio, 2),
                        "common_keywords": list(common)[:10],
                    })
    
    skills_report["potential_duplicates"] = len(overlaps)
    if overlaps:
        report["recommendations"].append(
            f"检测到 {len(overlaps)} 组潜在重复 Skill（关键词重叠 ≥50%）：\n" +
            "\n".join(
                f"  - {dup['a']} ↔ {dup['b']} ({dup['ratio']*100:.0f}% 重叠，关键词: {', '.join(dup['common_keywords'][:5])})"
                for dup in overlaps[:8]
            )
        )
        if len(overlaps) > 8:
            report["recommendations"][-1] += f"\n  ... 及其他 {len(overlaps) - 8} 组"
    
    # 检查 long tail：只被触发一次或从未被使用的 skills
    # (通过检查文件是否有 mtime 未变化来判断 —— 准确度有限，但比没有好)
    skills_report["checked_at"] = now.isoformat()
    report["skills"] = skills_report


# ═══════════════════════════════
# 磁盘清理辅助
# ═══════════════════════════════

def clean_temp_files():
    """清理 workspace 中的临时文件"""
    workspace = Path.home() / ".Hermes" / "workspace"
    if not workspace.exists():
        return
    
    cleaned = 0
    cleaned_size = 0
    
    for pattern in ["*.tmp", "*.log", "__pycache__", "*.pyc", ".pytest_cache", ".mypy_cache", ".ruff_cache"]:
        for f in workspace.rglob(pattern):
            if f.is_dir():
                try:
                    size = sum(p.stat().st_size for p in f.rglob("*") if p.is_file())
                    shutil.rmtree(f)
                    cleaned += 1
                    cleaned_size += size
                except (PermissionError, OSError):
                    pass
            else:
                try:
                    cleaned_size += f.stat().st_size
                    f.unlink()
                    cleaned += 1
                except (PermissionError, OSError):
                    pass
    
    if cleaned > 0:
        report["actions_taken"].append(f"清理临时文件: {cleaned} 项，释放 {cleaned_size / 1024:.0f} KB")
    
    # 清理空目录
    empty_dirs = []
    for root, dirs, _files in os.walk(workspace, topdown=False):
        for d in dirs:
            dirpath = Path(root) / d
            try:
                if not any(dirpath.iterdir()):
                    empty_dirs.append(dirpath)
            except (PermissionError, OSError):
                continue
    
    for d in empty_dirs:
        try:
            d.rmdir()
        except (PermissionError, OSError):
            pass
    
    if empty_dirs:
        report["actions_taken"].append(f"移除 {len(empty_dirs)} 个空目录")


# ═══════════════════════════════
# 主流程
# ═══════════════════════════════

def main():
    maintain_memory()
    maintain_skills()
    clean_temp_files()
    
    # 最终输出为 JSON + 可读摘要
    print(json.dumps(report, ensure_ascii=False, indent=2))
    
    # 打印可读摘要到 stderr（方便 cron 日志）
    import sys
    print("\n" + "="*60, file=sys.stderr)
    print(f"📋 维护报告 [{now.strftime('%Y-%m-%d %H:%M')}]", file=sys.stderr)
    print(f"内存: {report['memory'].get('usage_pct', 'N/A')}% | "
          f"Skills: {report['skills'].get('total_count', 'N/A')}/{SKILL_WARN_LIMIT}", file=sys.stderr)
    if report["warnings"]:
        print(f"⚠️  {len(report['warnings'])} 条警告", file=sys.stderr)
    if report["actions_taken"]:
        print(f"✅  {len(report['actions_taken'])} 项操作已执行", file=sys.stderr)
    if report["recommendations"]:
        print(f"💡  {len(report['recommendations'])} 条建议", file=sys.stderr)
    print("="*60, file=sys.stderr)


if __name__ == "__main__":
    main()
