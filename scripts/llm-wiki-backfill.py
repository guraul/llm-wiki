#!/usr/bin/env python3
"""精细回填：只追加新字段，保持原有 frontmatter 格式不变。
遵守 ADR-001 安全写入规则：
1. 用 YAML parser 解析验证（不手动字符串替换）
2. 写入前保留原文（已有备份）
3. atomic write（先写 .tmp 再 mv）
4. git diff 可审查（只追加，不重排已有字段）
"""
import os
import re
import shutil
from pathlib import Path
import yaml

VAULT = Path("/Users/gubin/workspace/gbwikis")
WIKI = VAULT / "wiki"
BACKUP_DIR = VAULT / ".lint-backup-20260719"

SUB_TO_KTYPE = {
    "concepts": "concept",
    "entities": "entity",
    "decisions": "decision",
    "patterns": "pattern",
    "problems": "problem",
    "procedures": "procedure",
    "synthesis": "reference",
}

def parse_frontmatter_text(content):
    """解析 frontmatter，返回 (fm_dict, fm_text, body_text)"""
    if not content.startswith("---"):
        return {}, "", content
    # 找第二个 ---
    end_match = re.search(r"\n---\s*\n", content[3:])
    if not end_match:
        return {}, "", content
    fm_text = content[3:3 + end_match.start() + 1]
    body = content[3 + end_match.end():]
    try:
        fm = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError as e:
        print(f"  ERROR parsing: {e}")
        return {}, "", content
    return fm, fm_text, body

def infer_confidence(sources):
    if not sources:
        return {"level": "low", "reason": "inferred synthesis, no direct source cited"}
    if len(sources) >= 2:
        return {"level": "high", "reason": "multiple sources corroborate"}
    src = str(sources[0]).lower()
    if "sop" in src or "official" in src:
        return {"level": "high", "reason": "standard operating procedure / official reference"}
    if "report" in src or "summary" in src:
        return {"level": "medium", "reason": "single technical report or session summary"}
    if "issue" in src or "problem" in src:
        return {"level": "medium", "reason": "single issue record"}
    return {"level": "medium", "reason": "single source, not independently verified"}

def build_evidence(sources, content):
    evidence = []
    if sources:
        for s in sources:
            if isinstance(s, str):
                src_str = s if s.startswith("[[") else f"[[{s}]]"
                evidence.append({
                    "source": src_str,
                    "quote": "(see source page for details)",
                    "confidence": "medium",
                })
    else:
        links = re.findall(r"\[\[([^\]|#]+\.md)\]\]", content)
        seen = set()
        for link in links:
            basename = Path(link).name
            if basename not in seen and "source-" in basename:
                seen.add(basename)
                evidence.append({
                    "source": f"[[{link}]]",
                    "quote": "(referenced in body)",
                    "confidence": "medium",
                })
        if not evidence:
            evidence.append({
                "source": "(none)",
                "quote": "no explicit source; synthesized from existing knowledge",
                "confidence": "low",
            })
    return evidence

def format_new_fields(ktype, evidence, conf, updated):
    """把新字段格式化为 YAML 文本（block 格式，追加到已有 frontmatter 末尾）"""
    lines = []
    lines.append(f"knowledge_type: {ktype}")
    lines.append("evidence:")
    for e in evidence:
        lines.append(f"  - source: '{e['source']}'")
        lines.append(f"    quote: \"{e['quote']}\"")
        lines.append(f"    confidence: {e['confidence']}")
    lines.append("confidence:")
    lines.append(f"  level: {conf['level']}")
    lines.append(f"  reason: \"{conf['reason']}\"")
    # updated 是覆盖已有字段，需要单独处理
    return "\n".join(lines)

def atomic_write(path, content):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)

def process_page(path, sub):
    content = path.read_text(encoding="utf-8")
    fm, fm_text, body = parse_frontmatter_text(content)
    
    if "knowledge_type" in fm:
        print(f"  SKIP {sub}/{path.name} (already has knowledge_type)")
        return False
    
    # 备份
    backup_path = BACKUP_DIR / f"{sub}_{path.name}"
    if not backup_path.exists():
        shutil.copy2(path, backup_path)
    
    ktype = SUB_TO_KTYPE.get(sub, "reference")
    sources = fm.get("sources", [])
    if sources and not isinstance(sources, list):
        sources = [sources]
    evidence = build_evidence(sources, content)
    conf = infer_confidence(sources)
    
    # 构造新字段文本
    new_fields = format_new_fields(ktype, evidence, conf, "2026-07-19")
    
    # 处理 updated 字段：如果已有 updated，替换；否则追加
    original_updated = fm.get("updated")
    if original_updated and str(original_updated) != "2026-07-19":
        # 替换 updated 行（保持原格式，不加引号）
        updated_pattern = re.compile(r"^updated:\s*.+$", re.MULTILINE)
        new_fm_text = updated_pattern.sub("updated: 2026-07-19", fm_text)
        if new_fm_text == fm_text:
            # 没匹配到（可能是日期格式不同），追加
            new_fm_text = fm_text.rstrip() + "\nupdated: 2026-07-19"
    elif not original_updated:
        new_fm_text = fm_text.rstrip() + "\nupdated: 2026-07-19"
    else:
        new_fm_text = fm_text.rstrip()
    
    # 在 frontmatter 末尾追加新字段（紧接 updated 之后，不加额外空行）
    new_fm_text = new_fm_text + "\n" + new_fields
    
    # 重组文件（保持 ---\n 紧跟 frontmatter，不加空行）
    new_content = f"---\n{new_fm_text}\n---\n{body}"
    
    # 验证最终 frontmatter 可解析
    try:
        verify_fm = yaml.safe_load(new_fm_text)
        if "knowledge_type" not in verify_fm or "evidence" not in verify_fm or "confidence" not in verify_fm:
            print(f"  ERROR verification failed for {path.name}")
            return False
    except yaml.YAMLError as e:
        print(f"  ERROR verification parse failed: {e}")
        return False
    
    # atomic write
    atomic_write(path, new_content)
    
    print(f"  OK   {sub}/{path.name} → ktype={ktype}, evidence={len(evidence)}, conf={conf['level']}")
    return True

def main():
    print("=" * 60)
    print("精细回填 knowledge_type / evidence / confidence（保持原格式）")
    print(f"Vault: {VAULT}")
    print(f"备份: {BACKUP_DIR}")
    print("=" * 60)
    
    total = modified = 0
    for sub in ["concepts", "entities", "synthesis"]:
        d = WIKI / sub
        if not d.exists():
            continue
        print(f"\n--- {sub}/ ---")
        for f in sorted(d.glob("*.md")):
            total += 1
            if process_page(f, sub):
                modified += 1
    
    print(f"\n{'=' * 60}")
    print(f"总计: {total}, 修改: {modified}, 跳过: {total - modified}")
    print(f"备份: {BACKUP_DIR}")

if __name__ == "__main__":
    main()
