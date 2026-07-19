#!/usr/bin/env python3
"""LLM Wiki lint script - 按 SKILL.md 新版规则检查 vault 健康状态"""
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

VAULT = Path("/Users/gubin/workspace/gbwikis")
WIKI = VAULT / "wiki"

# 收集所有 wiki 页面
pages = {}
for sub in ["concepts", "entities", "decisions", "patterns", "problems", "procedures", "sources", "outputs", "synthesis"]:
    d = WIKI / sub
    if d.exists():
        for f in d.glob("*.md"):
            pages[f.name] = {"path": f, "sub": sub, "content": f.read_text(encoding="utf-8")}

# 也加 index.md
idx = WIKI / "index.md"
if idx.exists():
    pages["index.md"] = {"path": idx, "sub": "root", "content": idx.read_text(encoding="utf-8")}

# 解析 frontmatter (简易 YAML 解析，只取关键字段)
def parse_fm(content):
    if not content.startswith("---"):
        return {}, content
    end = content.find("\n---", 3)
    if end < 0:
        return {}, content
    fm_text = content[3:end].strip()
    body = content[end+4:]
    fm = {}
    current_key = None
    current_list = None
    for line in fm_text.split("\n"):
        if line.startswith("  - ") and current_key:
            # list item
            item = line[4:].strip().strip('"').strip("'")
            if current_list is None:
                current_list = []
            current_list.append(item)
        elif ":" in line and not line.startswith(" "):
            if current_key and current_list is not None:
                fm[current_key] = current_list
                current_list = None
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if val:
                fm[key] = val
                current_key = key
                current_list = None
            else:
                current_key = key
                current_list = [] if key in ("sources", "aliases", "tags") else None
    if current_key and current_list is not None:
        fm[current_key] = current_list
    return fm, body

# 解析所有页面
parsed = {}
for name, info in pages.items():
    fm, body = parse_fm(info["content"])
    parsed[name] = {**info, "fm": fm, "body": body, "chars": len(info["content"])}

# 检查 1: 孤立页面 (无入站链接)
wikilink_re = re.compile(r"\[\[([^\]|#]+)")
inbound = {name: 0 for name in parsed}
for name, info in parsed.items():
    for m in wikilink_re.finditer(info["content"]):
        target = m.group(1).strip()
        # 标准化：去掉路径前缀
        target_basename = Path(target).name
        if target_basename in inbound and target_basename != name:
            inbound[target_basename] += 1

orphans = [n for n, c in inbound.items() if c == 0 and n != "index.md"]

# 检查 2: 缺失引用 (frontmatter sources 指向不存在的文件)
missing_refs = []
for name, info in parsed.items():
    srcs = info["fm"].get("sources", [])
    if isinstance(srcs, list):
        for s in srcs:
            # 提取 [[xxx.md]] 中的文件名
            m = re.search(r"\[\[([^\]]+)\]\]", s)
            target = m.group(1) if m else s
            target_basename = Path(target).name
            if target_basename not in parsed:
                missing_refs.append((name, s))

# 检查 3: 过时信息 (updated > 30 天)
now = datetime.now()
threshold = now - timedelta(days=30)
outdated = []
for name, info in parsed.items():
    upd = info["fm"].get("updated") or info["fm"].get("created")
    if upd:
        try:
            d = datetime.strptime(str(upp)[:10] if 'upp' in dir() else str(upd)[:10], "%Y-%m-%d")
            if d < threshold:
                outdated.append((name, str(upd)[:10]))
        except Exception:
            pass

# 检查 4: 空页面 (< 100 字符)
empty = [(n, info["chars"]) for n, info in parsed.items() if info["chars"] < 100]

# 检查 5: 重复概念 (标题/aliases 相似)
titles = {}
for name, info in parsed.items():
    title = name.replace(".md", "")
    aliases = info["fm"].get("aliases", [])
    if isinstance(aliases, list):
        for a in aliases:
            titles.setdefault(a.lower(), []).append(name)
    titles.setdefault(title.lower(), []).append(name)
duplicates = {k: v for k, v in titles.items() if len(set(v)) > 1}

# 检查 6: 低证据事实 (low confidence 但写成事实) - 简化检查：看是否有 confidence 字段且为 low
low_confidence = []
for name, info in parsed.items():
    conf = info["fm"].get("confidence")
    if isinstance(conf, dict):
        level = conf.get("level", "").lower()
    else:
        level = str(conf or "").lower()
    if level == "low":
        low_confidence.append(name)

# 检查 7: 缺少 knowledge_type (非 source/output 页面)
missing_ktype = []
for name, info in parsed.items():
    if info["sub"] in ("sources", "outputs", "root"):
        continue
    if "knowledge_type" not in info["fm"]:
        missing_ktype.append(name)

# 检查 8: 缺少 evidence 字段 (durable 页面)
missing_evidence = []
for name, info in parsed.items():
    if info["sub"] in ("sources", "outputs", "root"):
        continue
    if "evidence" not in info["fm"]:
        missing_evidence.append(name)

# 生成报告
print("=" * 60)
print("LLM Wiki 健康检查报告")
print(f"扫描时间: {now.strftime('%Y-%m-%d %H:%M')}")
print(f"Vault: {VAULT}")
print(f"页面总数: {len(parsed)}")
print(f"  - concepts: {sum(1 for i in parsed.values() if i['sub']=='concepts')}")
print(f"  - entities: {sum(1 for i in parsed.values() if i['sub']=='entities')}")
print(f"  - sources:  {sum(1 for i in parsed.values() if i['sub']=='sources')}")
print(f"  - outputs:  {sum(1 for i in parsed.values() if i['sub']=='outputs')}")
print(f"  - synthesis:{sum(1 for i in parsed.values() if i['sub']=='synthesis')}")
print(f"  - decisions/patterns/problems/procedures: 0 (目录不存在)")
print("=" * 60)

print(f"\n### 孤立页面 ({len(orphans)} 个)")
for o in orphans:
    print(f"  - {o}（无入站链接）")

print(f"\n### 缺失引用 ({len(missing_refs)} 个)")
for src, ref in missing_refs[:20]:
    print(f"  - {src} → {ref}")

print(f"\n### 可能过时 ({len(outdated)} 个, updated > 30 天)")
for name, d in outdated:
    print(f"  - {name}（最后更新: {d}）")

print(f"\n### 空页面 ({len(empty)} 个, < 100 字符)")
for name, c in empty:
    print(f"  - {name}（{c} 字符）")

print(f"\n### 重复概念 ({len(duplicates)} 组)")
for k, v in duplicates.items():
    print(f"  - '{k}' 出现在: {v}")

print(f"\n### 低证据事实 ({len(low_confidence)} 个)")
for n in low_confidence:
    print(f"  - {n}")

print(f"\n### 缺少 knowledge_type ({len(missing_ktype)} 个)")
for n in missing_ktype:
    print(f"  - {n}")

print(f"\n### 缺少 evidence 字段 ({len(missing_evidence)} 个)")
for n in missing_evidence:
    print(f"  - {n}")

print("\n" + "=" * 60)
print("### 建议")
print("1. 创建新目录: wiki/decisions/ wiki/patterns/ wiki/problems/ wiki/procedures/")
print("2. 为 durable 页面补充 knowledge_type 和 evidence 字段")
print("3. 修复缺失引用或修正链接")
print("4. 处理孤立页面（补充内容或建立入站链接）")
print("5. 过时页面重新评估是否需要更新")
