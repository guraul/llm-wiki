---
name: llm-wiki
description: LLM Wiki 知识库维护。当用户说"导入"、"添加到 wiki"、"处理 wiki"、"查询 wiki"、"检查 wiki"、"lint wiki"、"编译 wiki"时触发。读取 AGENTS.md 中的 LLM_WIKI_VAULT 来确定 vault 路径。
---

# LLM Wiki Skill

基于 Karpathy 的 LLM Wiki 思想和 luotwo/llm-wiki 实战经验。

## 核心理念

传统 RAG 每次查询都重新检索，知识不积累。LLM Wiki 让知识持久化、结构化、复利增长：
- 每添加一个来源，可能更新 10-15 个页面
- 交叉引用自动建立，矛盾自动标注
- 查询答案可选择保存为新页面

## 触发条件

用户可能说：
- "导入 raw/inbox/article.md"
- "把这篇文章添加到 wiki"
- "处理 wiki"
- "编译 wiki"
- "查询 wiki 中关于 X 的内容"
- "wiki 中有什么关于 Y 的"
- "检查 wiki 健康状态"
- "lint wiki"

## 获取 vault 路径

**关键步骤**：在执行任何操作前，先确认 vault 路径。

### 步骤

1. 使用 Bash tool 检查 `AGENTS.md` 中的 `LLM_WIKI_VAULT`：

   ```bash
   grep -i 'LLM_WIKI_VAULT' AGENTS.md 2>/dev/null | head -1 || echo "NOT_FOUND"
   ```

   如果输出格式如 `LLM_WIKI_VAULT="/path/to/vault"`，提取其中的路径。
   使用 Bash tool 验证该路径是否包含 `.obsidian/`：

   ```bash
   ls -la "$LLM_WIKI_VAULT/.obsidian/" 2>/dev/null && echo "VAULT_OK" || echo "INVALID_VAULT"
   ```

   - 如果存在（输出 `VAULT_OK`）→ vault 路径 = `$LLM_WIKI_VAULT`
   - 如果不存在（输出 `INVALID_VAULT`）→ **报错终止**："AGENTS.md 中 LLM_WIKI_VAULT 路径无效：{路径}"

2. 如果 AGENTS.md 中找不到 `LLM_WIKI_VAULT`（输出 `NOT_FOUND`）→ **报错终止**："请在 AGENTS.md 中设置 LLM_WIKI_VAULT='/path/to/your/vault'"

3. vault 路径确认后，后续所有操作基于此路径。

## 目录结构

```
vault/
├── raw/
│   ├── inbox/        # 新资料放入此目录（支持 .md, .txt, .pdf, .html, .json, .csv）
│   ├── processed/    # 已处理的资料（LLM 移动至此）
│   └── assets/       # 图片（.png, .jpg, .webp）
├── wiki/
│   ├── index.md      # 自动更新的目录（L2 缓存）
│   ├── concepts/     # 概念页（如：Agent, RAG, MCP）
│   ├── entities/     # 实体/项目页（如：OpenCode, Obsidian）
│   ├── sources/      # 来源摘要页
│   ├── outputs/      # 保存的查询答案
│   └── synthesis/    # 综合分析页
├── log.md            # 时间线日志（追加记录）
└── .obsidian/        # Obsidian 配置（vault 标识）
```

**重要**：`raw/` 是不可变的，LLM 只读取不修改。`wiki/` 是 LLM 维护的区域。

## 页面命名规范

| 页面类型 | 命名格式 | 示例 |
|---------|---------|------|
| 来源摘要 | `source-{关键词}.md` | `source-cloudflare-ip.md` |
| 实体页 | `{实体名}.md` | `opencode.md`, `obsidian.md` |
| 概念页 | `{概念名}.md` | `agent.md`, `rag.md` |
| 工作流 | `{场景}-workflow.md` | `competitive-analysis-workflow.md` |
| 输出 | `{主题}-output-{日期}.md` | `cloudflare-vs-wechat-output-2026-04-14.md` |

命名规则：
- 使用英文或拼音，避免空格
- 小写字母，用 `-` 连接
- 关键词选择：从标题或内容提取核心词

## Frontmatter 模板

### 来源摘要页

```yaml
---
tags: [source-summary, 领域标签]
source: "原文标题"
author: 作者名（可选）
date: YYYY-MM-DD
url: "原始链接"（可选）
processed: YYYY-MM-DD
---
```

### 概念页/实体页

```yaml
---
tags: [concept 或 entity, 领域标签]
aliases: ["别名1", "别名2"]
sources:
  - "[[source-xxx.md]]"
  - "[[source-yyy.md]]"
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

### 输出页

```yaml
---
tags: [output, 查询类型]
query: "原始问题"
sources:
  - "[[source-xxx.md]]"
  - "[[concept-yyy.md]]"
created: YYYY-MM-DD
---
```

## 摄入流程（Ingest）

当用户说"导入"或"添加到 wiki"时执行：

> **IMPORTANT**：以下步骤必须全部执行，缺一不可。每一步完成后必须确认结果，不可跳过。

### 步骤 0：确认 vault 路径

按"获取 vault 路径"流程确认并设置变量 `$VAULT`。

### 步骤 1：读取文件（MUST）

- 如果用户指定文件：读取 `$VAULT/raw/inbox/{指定文件}`
- 如果用户说"导入所有"：使用 `ls $VAULT/raw/inbox/` 列出所有文件，逐一处理
- 支持格式：`.md, .txt, .pdf, .html, .json, .csv`
- 所有路径前面都要加 `$VAULT/`

### 步骤 2：创建来源摘要页（MUST）

- 在 `$VAULT/wiki/sources/` 创建 `source-{关键词}.md`
- 内容包括：标题、来源、核心内容摘要、关键观点
- 添加 frontmatter（tags, source, date, url）
- 底部添加：`## 来源\n- 原始文件：[[raw/inbox/xxx.md]]`

### 步骤 3：提取并创建概念/实体页（MUST）

分析内容，提取：
- **概念**：方法论、技术原理、设计模式等抽象概念
- **实体**：具体的项目、工具、公司、人物等

每个概念/实体：
- 如果 `$VAULT/wiki/concepts/{概念}.md` 或 `$VAULT/wiki/entities/{实体}.md` 已存在：更新内容（追加新观点，不覆盖）
- 如果不存在：创建新页面，包含定义、关键点、与相关概念的关系

### 步骤 4：建立交叉引用（MUST）

在创建/更新页面时：
- 使用 `[[wikilink]]` 链接到相关页面
- 在来源摘要页底部列出提取的概念：`## 相关概念\n- [[agent.md]]\n- [[rag.md]]`
- 在概念/实体页的 frontmatter 中添加来源链接

**交叉引用原则**：
- **共同主题**：多篇资料反复出现的观点 → 在概念页明确标注"多篇来源共识"
- **矛盾观点**：不同资料的冲突观点 → 标注"矛盾：来源A认为...，来源B认为..."
- **补充关系**：新资料补充已有概念 → 更新概念页，追加内容

### 步骤 5：更新 index.md（MUST）

读取 `$VAULT/wiki/index.md`，按类别追加新条目。如果该条目已存在则跳过。

```markdown
# Wiki Index

## 来源摘要
- [[sources/source-cloudflare-ip.md]] - Cloudflare 优选 IP 加速方案
- ...

## 实体
- [[entities/opencode.md]] - OpenCode CLI 工具
- ...

## 概念
- [[concepts/agent.md]] - Agent 设计模式
- ...

## 输出
- [[outputs/xxx-output-2026-04-14.md]] - 某查询的答案
- ...

## 综合分析
- [[synthesis/xxx.md]] - 某主题的综合分析
- ...
```

### 步骤 6：记录 log.md（MUST）

在 `$VAULT/log.md` 追加：

```markdown
## [YYYY-MM-DD HH:MM] ingest | {文件名}
- 创建来源摘要：[[sources/source-xxx.md]]
- 创建/更新概念页：[[concepts/aaa.md]], [[concepts/bbb.md]]
- 创建/更新实体页：[[entities/ccc.md]]
- 建立交叉引用：N 个
```

### 步骤 7：移动文件（MUST）

将处理完成的文件从 `$VAULT/raw/inbox/` 移动到 `$VAULT/raw/processed/`：

```bash
mv "$VAULT/raw/inbox/{文件名}" "$VAULT/raw/processed/"
```

**注意**：如果用户指定了特定文件，只移动该文件。如果是批量处理，逐个移动。

### 步骤 8：校验（MUST）

执行以下检查，确认所有步骤已完成：

```bash
# 检查来源摘要页是否存在
ls "$VAULT/wiki/sources/source-{关键词}.md"
# 检查 index.md 是否包含新条目
grep "source-{关键词}" "$VAULT/wiki/index.md"
# 检查 log.md 是否有本次记录
tail -5 "$VAULT/log.md"
# 确认 inbox 文件已移走
ls "$VAULT/raw/inbox/{文件名}" 2>/dev/null && echo "ERROR: 文件未移动" || echo "OK: 已移走"
```

如果校验失败，必须修正错误后才能告知用户完成。

## 查询流程（Query）

当用户说"查询 wiki"或在 wiki 中提问时执行：

### 步骤 0：确认 vault 路径

按"获取 vault 路径"流程确认。

### 步骤 1：定位相关页面

使用 Bash tool：`ls "$VAULT/wiki/" "$VAULT/wiki/concepts/" "$VAULT/wiki/entities/" "$VAULT/wiki/sources/"`

然后读取 `$VAULT/wiki/index.md`，根据问题关键词定位相关页面类别。

### 步骤 2：读取相关页面

根据 index.md 的指引，读取最相关的 3-5 个页面：
- 如果问题涉及具体概念 → 读取 `$VAULT/wiki/concepts/{概念}.md`
- 如果问题涉及具体实体 → 读取 `$VAULT/wiki/entities/{实体}.md`
- 如果问题需要对比 → 读取多个相关页面

**缓存层级**：
- L1（最快）：Skill 指令（本文件）
- L2：index.md（目录定位）
- L3：具体页面（详细内容）

优先读 L2 定位，再深入 L3。

### 步骤 3：综合回答

基于读取的内容，综合回答用户问题。回答中：
- 引用来源页面：`根据 [[sources/source-xxx.md]]，...`
- 引用概念页面：`[[concepts/agent.md]] 中提到...`

### 步骤 4：判断是否保存

**自动判断标准**：
- ✅ **保存**：综合分析、对比研究、方法论总结、有长期价值的内容
- ❌ **不保存**：简单问答、事实查询、临时性问题

如果判断保存：
- 在 `$VAULT/wiki/outputs/` 创建 `{主题}-output-{日期}.md`
- 内容包括：问题、答案、引用来源
- 添加 frontmatter（tags, query, sources, created）
- 更新 `$VAULT/wiki/index.md` 的"输出"部分
- 在 `$VAULT/log.md` 追加记录

## Lint 流程

当用户说"检查 wiki"或"lint wiki"时执行：

### 步骤 0：确认 vault 路径

按"获取 vault 路径"流程确认。

### 步骤 1：列出所有页面

使用 Bash tool：
```bash
ls "$VAULT/wiki/"*.md "$VAULT/wiki/concepts/"*.md "$VAULT/wiki/entities/"*.md "$VAULT/wiki/sources/"*.md 2>/dev/null
```

### 步骤 2：检查问题

逐一检查：

| 问题类型 | 检查方法 | 报告格式 |
|---------|---------|---------|
| **孤立页面** | 页面无入站链接（无其他页面引用它） | `孤立页面：xxx.md（无入站链接）` |
| **缺失引用** | frontmatter 中 sources 列出的链接不存在 | `缺失引用：xxx.md → [[source-yyy.md]] 不存在` |
| **矛盾观点** | 不同页面中对同一概念有冲突描述 | `矛盾：[[concepts/a.md]] 与 [[concepts/b.md]] 对 X 的描述冲突` |
| **过时信息** | 页面 updated 时间超过 30 天且来源有更新 | `可能过时：xxx.md（最后更新：YYYY-MM-DD）` |
| **空页面** | 页面内容少于 100 字符 | `空页面：xxx.md（内容不足）` |

### 步骤 3：生成报告

在终端输出检查结果，格式：

```
## Wiki 健康检查报告

### 孤立页面（N 个）
- xxx.md
- yyy.md

### 缺失引用（N 个）
- ...

### 矛盾观点（N 个）
- ...

### 可能过时（N 个）
- ...

### 空页面（N 个）
- ...

### 建议
1. 处理孤立页面：删除或补充内容使其被引用
2. 修复缺失引用：创建被引用的页面或修正链接
3. 解决矛盾观点：标注矛盾并补充证据
4. 更新过时页面：重新处理相关来源
```

### 步骤 4：记录 log.md

在 `$VAULT/log.md` 追加：

```markdown
## [YYYY-MM-DD HH:MM] lint | 健康检查
- 孤立页面：N 个
- 缺失引用：N 个
- 矛盾观点：N 个
- 可能过时：N 个
- 空页面：N 个
```

## 缓存层级

为了提高查询效率，采用三层缓存：

| 层级 | 内容 | 读取时机 |
|------|------|---------|
| **L1** | Skill 指令（本文件） | 每次触发时已加载 |
| **L2** | $VAULT/wiki/index.md | 定位相关页面时 |
| **L3** | 具体页面（concepts/entities/sources） | 需要详细内容时 |

**查询流程**：
1. 已有 L1（Skill）
2. 读 L2（index.md）定位类别
3. 根据定位读 L3（具体页面）
4. 不需要遍历所有页面

## 支持的文件格式

| 格式 | 扩展名 | 处理方式 |
|------|--------|---------|
| Markdown | `.md` | 直接读取 |
| 纯文本 | `.txt` | 直接读取 |
| PDF | `.pdf` | 需要 PDF 解析（告知用户暂不支持或尝试读取） |
| HTML | `.html` | 尝试提取文本内容 |
| JSON | `.json` | 解析结构化数据 |
| CSV | `.csv` | 解析表格数据 |

## 工作流程示意

```
用户："导入 raw/inbox/article.md"
    ↓
[步骤 0] 确认 vault 路径（读取 AGENTS.md 中的 LLM_WIKI_VAULT）
    ↓
[步骤 1] 读取 $VAULT/raw/inbox/article.md
    ↓
[步骤 2] 创建 $VAULT/wiki/sources/source-xxx.md
    ↓
[步骤 3] 提取概念/实体 → 创建/更新 $VAULT/wiki/concepts/ 和 $VAULT/wiki/entities/
    ↓
[步骤 4] 建立 [[wikilink]] 交叉引用
    ↓
[步骤 5] 更新 $VAULT/wiki/index.md
    ↓
[步骤 6] 记录 $VAULT/log.md
    ↓
[步骤 7] mv $VAULT/raw/inbox/ → $VAULT/raw/processed/
    ↓
完成，告知用户处理结果
```

## 重要原则

1. **不覆盖已有内容**：更新页面时追加，不删除已有内容
2. **标注来源**：每个观点都要追溯来源
3. **标注矛盾**：发现矛盾要明确标注，不做判断
4. **保持简洁**：摘要页聚焦核心观点，不过度展开
5. **wikilink 优先**：使用 Obsidian 的 `[[wikilink]]` 格式
6. **移动而非删除**：处理后移动到 `$VAULT/raw/processed/`，保留原始资料

## 使用边界

本 skill **不会主动判断**哪些资料值得入库。以下指引供用户参考：

### ✅ 值得入库

- 技术方案调研、架构决策
- 踩坑记录、问题排查过程
- 配置参数、API 用法备忘
- 多方案对比分析
- 需要跨会话反复查阅的资料

### ❌ 不建议入库

- 一次性临时信息（日报、临时修复）
- AI 已熟练掌握的标准知识（通用 API、流行框架用法）
- 隐私敏感内容
- 时效性极短的信息

> 用户决定丢什么到 `raw/inbox/`，skill 负责处理。