# LLM Wiki Skill

基于 Karpathy LLM Wiki 思想的知识库管理技能。自动将原始资料提取、结构化、建立交叉引用，存入 Obsidian vault。

## 支持的 AI 工具

| 工具 | 安装位置 | 说明 |
|------|----------|------|
| **opencode** | `~/.config/opencode/skills/llm-wiki/SKILL.md` | 原生兼容 |
| **CodeBuddy/WorkBuddy** | `~/.codebuddy/skills/llm-wiki/SKILL.md` | 兼容 |

## 安装

### 一键安装

```bash
curl -fsSL https://raw.githubusercontent.com/guraul/llm-wiki/main/install.sh | bash
```

### 手动安装

```bash
# 1. 克隆仓库
git clone git@github.com:guraul/llm-wiki.git /tmp/llm-wiki

# 2. 安装到对应工具
# opencode
mkdir -p ~/.config/opencode/skills/llm-wiki/
cp /tmp/llm-wiki/opencode/SKILL.md ~/.config/opencode/skills/llm-wiki/SKILL.md

# CodeBuddy/WorkBuddy（可选）
mkdir -p ~/.codebuddy/skills/llm-wiki/
ln -s ~/.config/opencode/skills/llm-wiki/SKILL.md ~/.codebuddy/skills/llm-wiki/SKILL.md
```

## 配置

在 **Obsidian vault 根目录** 的 `AGENTS.md` 中添加：

```env
LLM_WIKI_VAULT="/path/to/your/obsidian/vault"
```

## 用法

在 vault 目录中运行 AI 工具，然后说：

| 命令 | 功能 |
|------|------|
| "导入 raw/inbox/article.md" | 导入单篇资料到 wiki |
| "导入 raw/inbox 中所有文件到 wiki" | 批量导入 |
| "查询 wiki 中关于 xxx 的内容" | 查询已入库知识 |
| "检查 wiki" | 健康检查（孤立页面、断链等） |

## 目录结构

```
vault/
├── AGENTS.md                    # LLM_WIKI_VAULT 配置
├── raw/
│   ├── inbox/                   # 放待处理的资料
│   ├── processed/               # 已处理的资料（LLM 自动移入）
│   └── assets/                  # 图片等资源
├── wiki/
│   ├── index.md                 # 自动更新的目录
│   ├── sources/                 # 来源摘要页
│   ├── concepts/                # 概念页
│   ├── entities/                # 实体/项目页
│   ├── outputs/                 # 查询答案存档
│   └── synthesis/               # 综合分析
└── log.md                       # 操作日志
```

## 原理

> **The Model IS the Agent. The Code is the Harness.**

传统 RAG 每次查询都重新检索，知识不积累。LLM Wiki 让知识持久化、结构化、复利增长——每添加一份资料，自动更新相关页面、建立交叉引用、标注矛盾观点。
