#!/usr/bin/env bash
set -euo pipefail

REPO="guraul/llm-wiki"
BRANCH="main"
TMP_DIR=$(mktemp -d)

cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

echo "📦 下载 LLM Wiki Skill..."
git clone --depth 1 -b "$BRANCH" "git@github.com:$REPO.git" "$TMP_DIR" 2>/dev/null || \
  git clone --depth 1 -b "$BRANCH" "https://github.com/$REPO.git" "$TMP_DIR"

# opencode
mkdir -p ~/.config/opencode/skills/llm-wiki/
cp "$TMP_DIR/opencode/SKILL.md" ~/.config/opencode/skills/llm-wiki/SKILL.md
echo "  ✅ opencode: ~/.config/opencode/skills/llm-wiki/SKILL.md"

# CodeBuddy/WorkBuddy（可选，兼容）
if command -v codebuddy &>/dev/null || command -v workbuddy &>/dev/null; then
  mkdir -p ~/.codebuddy/skills/llm-wiki/
  cp "$TMP_DIR/opencode/SKILL.md" ~/.codebuddy/skills/llm-wiki/SKILL.md
  echo "  ✅ CodeBuddy: ~/.codebuddy/skills/llm-wiki/SKILL.md"
fi

echo ""
echo "🎉 安装完成！"
echo ""
echo "下一步：在 Obsidian vault 根目录的 AGENTS.md 中添加："
echo "  LLM_WIKI_VAULT=\"/path/to/your/vault\""
echo ""
echo "然后在该目录运行 opencode 并说："
echo "  \"导入 raw/inbox 中所有文件到 wiki\""
