# LLM Wiki Skill

基于 Karpathy LLM Wiki 思想的知识库管理技能。自动将原始资料提取、规划、重编译、建立交叉引用，存入 Obsidian vault。

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

### 前提：启动 MCP 搜索服务

查询功能依赖 MCP 服务器 `llm-wiki-mcp` 提供全文检索。安装：

```bash
# 1. 克隆
git clone git@github.com:guraul/llm-wiki-mcp.git ~/llm-wiki-mcp

# 2. 安装依赖（需 Node.js 20+）
cd ~/llm-wiki-mcp
pnpm install
pnpm build
```

注册到 opencode，编辑 `~/.config/opencode/opencode.json`：

```json
{
  "mcp": {
    "wiki-query": {
      "type": "local",
      "command": ["node", "/path/to/llm-wiki-mcp/dist/index.js", "--vault-path", "/path/to/your/vault"]
    }
  }
}
```

重启 opencode 后生效。

### 日常使用

在 vault 目录中运行 opencode，然后说：

| 命令 | 功能 |
|------|------|
| "导入 raw/inbox/article.md" | 导入单篇资料到 wiki |
| "导入 raw/inbox 中所有文件到 wiki" | 批量导入 |
| "查询 wiki 中关于 xxx 的内容" | 全文检索已入库知识 |
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
│   ├── decisions/               # 架构/产品/技术决策
│   ├── patterns/                # 可复用方案、工作流、设计模式
│   ├── problems/                # 问题、限制、踩坑、风险
│   ├── procedures/              # 操作步骤、迁移流程、配置清单
│   ├── outputs/                 # 查询答案存档
│   └── synthesis/               # 综合分析
└── log.md                       # 操作日志
```

## 原理

> **The Model IS the Agent. The Code is the Harness.**

传统 RAG 每次查询都重新检索，知识不积累。LLM Wiki 让知识持久化、结构化、复利增长。

本项目的核心流程是：

```text
Raw document
  -> Source summary
  -> Knowledge planner
  -> Knowledge compiler
  -> Link update
  -> Wiki rewrite
```

每添加一份资料，skill 会先规划需要创建、重写、链接或标注冲突的页面，再把新证据编译进已有 wiki。更新页面时不盲目追加，而是重写受影响页面，保留有价值旧内容，合并重复信息，标注过时和低置信度内容。

更多设计见 [docs/prompt-pipeline.md](docs/prompt-pipeline.md)。
