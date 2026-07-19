---
name: llm-wiki
description: LLM Wiki 知识库维护。当用户说"导入"、"添加到 wiki"、"处理 wiki"、"查询 wiki"、"检查 wiki"、"lint wiki"、"编译 wiki"时触发。先读取环境变量 $LLM_WIKI_VAULT，再读取 AGENTS.md 中的 LLM_WIKI_VAULT（优先级更高）。
---

# LLM Wiki Skill

基于 Karpathy 的 LLM Wiki 思想和 luotwo/llm-wiki 实战经验。

## 核心理念

传统 RAG 每次查询都重新检索，知识不积累。LLM Wiki 让知识持久化、结构化、复利增长：
- 每添加一个来源，可能更新 10-15 个页面
- 交叉引用自动建立，矛盾自动标注
- 查询答案可选择保存为新页面

本 skill 的核心不是"把新内容追加到旧页面"，而是一次小型知识编译：
1. 读取新证据和已有页面
2. 规划需要创建、更新、合并、链接的页面
3. 重写受影响页面，使 wiki 保持一致、简洁、可追溯

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

优先级：**项目 AGENTS.md > 环境变量 $LLM_WIKI_VAULT**

### 步骤

> **说明**：环境变量 `$LLM_WIKI_VAULT` 优先级低于 `AGENTS.md`。
> 如果设置了 env var 但仍读不到（某些非交互 shell 不加载 `.zshrc`），
> 建议将 `export LLM_WIKI_VAULT=...` 放到 `~/.zshenv`（zsh 始终加载），
> 或在 macOS 上用 `launchctl setenv LLM_WIKI_VAULT /path/to/vault`。
> 路径如有空格或特殊字符，务必用双引号包裹变量引用。

1. 读取环境变量 `$LLM_WIKI_VAULT`：

   ```bash
   echo "${LLM_WIKI_VAULT:-EMPTY}"
   ```

   如果输出 `EMPTY`，尝试从 shell 配置文件中 grep：

   ```bash
   grep -i 'LLM_WIKI_VAULT' ~/.zshenv ~/.zshrc ~/.bashrc 2>/dev/null | head -1 || echo "NOT_FOUND"
   ```

   如果 grep 到了 `export LLM_WIKI_VAULT="..."`，提取其中的路径作为默认值。

2. 检查 `AGENTS.md` 中的 `LLM_WIKI_VAULT`（优先级更高）：

   ```bash
   grep -i 'LLM_WIKI_VAULT' AGENTS.md 2>/dev/null | head -1 || echo "NOT_FOUND"
   ```

   如果输出了 `LLM_WIKI_VAULT="..."`，用此值**覆盖**第 1 步中读取的值。

3. 确定最终 vault 路径：

   - 如果第 2 步在 AGENTS.md 中找到 → 使用 `$VAULT` = AGENTS.md 中的值
   - 否则如果第 1 步找到有效路径 → 使用 `$VAULT` = 该路径
   - 如果两者都未设置 → **报错终止**："请在 AGENTS.md 中设置 LLM_WIKI_VAULT，或设置环境变量 $LLM_WIKI_VAULT"

4. 验证该路径是否包含 `.obsidian/`：

   ```bash
   ls -la "$VAULT/.obsidian/" 2>/dev/null && echo "VAULT_OK" || echo "INVALID_VAULT"
   ```

   - 如果输出 `VAULT_OK` → vault 路径确认
   - 如果输出 `INVALID_VAULT` → **报错终止**："LLM_WIKI_VAULT 路径无效：{路径}"

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
│   ├── decisions/    # 架构/产品/技术决策
│   ├── patterns/     # 可复用方案、工作流、设计模式
│   ├── problems/     # 问题、限制、踩坑、风险
│   ├── procedures/   # 操作步骤、迁移步骤、配置流程
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
| 决策页 | `{决策关键词}-decision.md` | `hsc-migration-decision.md` |
| 模式页 | `{场景}-pattern.md` | `competitive-analysis-pattern.md` |
| 问题页 | `{问题关键词}-problem.md` | `password-migration-problem.md` |
| 流程页 | `{场景}-procedure.md` | `entra-id-setup-procedure.md` |
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
knowledge_type: concept 或 entity 或 decision 或 pattern 或 problem 或 procedure 或 reference
aliases: ["别名1", "别名2"]
sources:
  - "[[source-xxx.md]]"
  - "[[source-yyy.md]]"
evidence:
  - source: "[[source-xxx.md]]"
    quote: "支持该观点的短摘录或定位"
    confidence: high
confidence:
  level: high 或 medium 或 low
  reason: "official documentation / architecture decision / user note / inferred synthesis"
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

### 证据和置信度规则

- `high`：官方文档、源码、架构决策记录、明确的一手资料。
- `medium`：可信博客、会议资料、团队经验总结、多个来源互相印证。
- `low`：单一用户笔记、推测、口头结论、来源不完整的信息。
- 不确定内容不要写成事实，放入 `## Unverified assumptions` 或 `## Open questions`。

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
- 如果所需 wiki 子目录不存在，先创建：`sources/ concepts/ entities/ decisions/ patterns/ problems/ procedures/ outputs/ synthesis/`

### 步骤 2：创建来源摘要页（MUST）

- 在 `$VAULT/wiki/sources/` 创建 `source-{关键词}.md`
- 内容包括：标题、来源、核心内容摘要、关键观点、证据质量
- 添加 frontmatter（tags, source, date, url）
- 底部添加：`## 来源\n- 原始文件：[[raw/inbox/xxx.md]]`

### 步骤 3：Knowledge Planner（MUST）

在写入概念/实体/决策页面之前，必须先生成修改计划。计划不一定要保存成文件，但必须指导后续操作。

Planner 需要读取：
- 新来源摘要页
- `$VAULT/wiki/index.md`
- 已有相关页面（通过 index、文件名、全文搜索或 `rg` 定位）

Planner 输出结构：

```yaml
create:
  - path: wiki/concepts/example.md
    knowledge_type: concept
    reason: "new durable concept"
update:
  - path: wiki/problems/example-problem.md
    reason: "new evidence changes existing limitation"
rewrite:
  - path: wiki/concepts/existing.md
    reason: "deduplicate and merge new facts"
link:
  - from: wiki/concepts/a.md
    to: wiki/patterns/b-pattern.md
    relation: "uses"
conflicts:
  - page: wiki/concepts/example.md
    old: "old claim"
    new: "new claim"
    handling: "mark obsolete / prefer latest official source / keep both with context"
open_questions:
  - "missing source for ..."
```

如果 Planner 发现新资料和已有页面高度重复，优先更新或重写已有页面，不要创建近义重复页。

### 步骤 4：Knowledge Compiler（MUST）

根据 Planner 执行创建或更新。分析内容时至少区分以下知识类型：

| 类型 | 说明 | 默认目录 |
|------|------|---------|
| **Concept** | 方法论、技术原理、抽象概念 | `wiki/concepts/` |
| **Entity** | 项目、工具、公司、人物、产品 | `wiki/entities/` |
| **Decision** | 为什么选择某方案，以及取舍 | `wiki/decisions/` |
| **Pattern** | 可复用方案、工作流、设计模式 | `wiki/patterns/` |
| **Problem** | 限制、风险、踩坑、错误模式 | `wiki/problems/` |
| **Procedure** | 操作步骤、迁移流程、配置清单 | `wiki/procedures/` |
| **Reference** | 参数、API、命令、事实表 | 合适目录或 `wiki/synthesis/` |

每个 durable wiki 页面：
- 如果目标页面不存在：创建新页面，包含定义、用途、关键事实、证据、相关链接。
- 如果目标页面已存在：先读取完整旧页面，再用新证据重写页面。

**重写规则**：
- 保留仍然正确且有价值的旧内容。
- 合并重复信息，删除无用重复段落。
- 新事实要写入合适位置，不要堆在页面底部。
- 过时信息不要静默删除，必要时放入 `## Historical context` 或标注 obsolete。
- 矛盾信息要放入 `## Conflicts`，写清来源、时间、置信度和处理理由。
- 低置信度信息放入 `## Unverified assumptions`，不要伪装成确定事实。
- 页面 frontmatter 的 `sources`、`evidence`、`confidence`、`updated` 必须同步更新。
- **Never blindly append. Recompile the page.**

### 步骤 5：建立交叉引用（MUST）

在创建/更新页面时：
- 使用 `[[wikilink]]` 链接到相关页面
- 在来源摘要页底部列出提取的概念：`## 相关概念\n- [[agent.md]]\n- [[rag.md]]`
- 在概念/实体页的 frontmatter 中添加来源链接

**交叉引用原则**：
- **共同主题**：多篇资料反复出现的观点 → 在概念页明确标注"多篇来源共识"
- **矛盾观点**：不同资料的冲突观点 → 标注"矛盾：来源A认为...，来源B认为..."
- **补充关系**：新资料补充已有概念 → 重写概念页，将补充信息合并到合适章节
- **依赖关系**：A 需要 B 才成立 → 使用"依赖/前置条件/限制"等自然语言说明
- **替代关系**：A 替代 B 或 B 已过时 → 保留历史语境，避免混淆当前建议

### 步骤 6：更新 index.md（MUST）

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

## 决策
- [[decisions/hsc-migration-decision.md]] - HSC migration 方案选择
- ...

## 模式
- [[patterns/competitive-analysis-pattern.md]] - 竞品分析工作流
- ...

## 问题
- [[problems/password-migration-problem.md]] - 密码迁移限制
- ...

## 流程
- [[procedures/entra-id-setup-procedure.md]] - Entra ID 配置流程
- ...

## 输出
- [[outputs/xxx-output-2026-04-14.md]] - 某查询的答案
- ...

## 综合分析
- [[synthesis/xxx.md]] - 某主题的综合分析
- ...
```

### 步骤 7：记录 log.md（MUST）

在 `$VAULT/log.md` 追加：

```markdown
## [YYYY-MM-DD HH:MM] ingest | {文件名}
- 创建来源摘要：[[sources/source-xxx.md]]
- Planner：create N / rewrite N / link N / conflict N
- 创建页面：[[concepts/aaa.md]], [[patterns/bbb-pattern.md]]
- 重写页面：[[entities/ccc.md]], [[problems/ddd-problem.md]]
- 建立交叉引用：N 个
- 低置信度或未验证假设：N 个
```

### 步骤 8：移动文件（MUST）

将处理完成的文件从 `$VAULT/raw/inbox/` 移动到 `$VAULT/raw/processed/`：

```bash
mv "$VAULT/raw/inbox/{文件名}" "$VAULT/raw/processed/"
```

**注意**：如果用户指定了特定文件，只移动该文件。如果是批量处理，逐个移动。

### 步骤 9：校验（MUST）

执行以下检查，确认所有步骤已完成：

```bash
# 检查来源摘要页是否存在
ls "$VAULT/wiki/sources/source-{关键词}.md"
# 检查 index.md 是否包含新条目
grep "source-{关键词}" "$VAULT/wiki/index.md"
# 检查 log.md 是否有本次记录
tail -5 "$VAULT/log.md"
# 检查重写页面是否包含新来源
rg "source-{关键词}" "$VAULT/wiki"
# 确认 inbox 文件已移走
ls "$VAULT/raw/inbox/{文件名}" 2>/dev/null && echo "ERROR: 文件未移动" || echo "OK: 已移走"
```

如果校验失败，必须修正错误后才能告知用户完成。

## 查询流程（Query）

当用户说"查询 wiki"或在 wiki 中提问时执行：

### 步骤 0：确认 vault 路径

按"获取 vault 路径"流程确认。

### 步骤 1：定位入口页面

调用 `wiki-query` MCP server 的 `search_wiki` 工具搜索用户问题中的关键词，获取最相关的 5-10 个结果及其摘要。先找入口概念、实体、决策或问题页，而不是只找单个命中文档。

### 步骤 2：Agent Traversal 读取相关页面

根据搜索结果中的文件路径，读取最相关的 3-5 个页面（优先选中高分的）。然后沿页面内的 wikilink 继续读取必要页面：
- 使用 Read tool 读取完整内容
- 如果搜索结果不足，再读 `$VAULT/wiki/index.md` 补查
- 对"为什么选择 X"类问题，优先跟踪 `decisions/`、`problems/`、`patterns/`
- 对"如何做 X"类问题，优先跟踪 `procedures/`、`patterns/` 和相关概念页
- 对事实性问题，检查 `sources` 和 `confidence`，不要只引用低置信度页面

**缓存层级**：
- L1（最快）：Skill 指令（本文件）
- L2：MCP 全文搜索（`search_wiki`）
- L3：具体页面（详细内容）

优先走 L1 → L2 定位，再深入 L3。

### 步骤 3：综合回答

基于读取的内容，综合回答用户问题。回答中：
- 引用来源页面：`根据 [[sources/source-xxx.md]]，...`
- 引用概念页面：`[[concepts/agent.md]] 中提到...`
- 区分事实、推论、未验证假设
- 如果不同页面冲突，说明冲突和采用哪一侧的理由

### 步骤 4：判断是否保存

**自动判断标准**：
- ✅ **保存**：综合分析、对比研究、方法论总结、有长期价值的内容
- ❌ **不保存**：简单问答、事实查询、临时性问题

如果判断保存：
- 在 `$VAULT/wiki/outputs/` 创建 `{主题}-output-{日期}.md`，或在更适合的 `synthesis/` 页面中重写综合分析
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
ls "$VAULT/wiki/"*.md "$VAULT/wiki/concepts/"*.md "$VAULT/wiki/entities/"*.md "$VAULT/wiki/decisions/"*.md "$VAULT/wiki/patterns/"*.md "$VAULT/wiki/problems/"*.md "$VAULT/wiki/procedures/"*.md "$VAULT/wiki/sources/"*.md 2>/dev/null
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
| **重复概念** | 标题、aliases、正文高度相似，或互为近义词 | `重复概念：xxx.md 与 yyy.md 可能应合并` |
| **低证据事实** | 页面把 low confidence 或 user note 写成确定事实 | `低证据事实：xxx.md 中 Y 缺少可靠来源` |
| **缺少知识类型** | 非 source/output 页面缺少 `knowledge_type` | `缺少知识类型：xxx.md` |

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

### 重复概念（N 个）
- ...

### 低证据事实（N 个）
- ...

### 缺少知识类型（N 个）
- ...

### 建议
1. 处理孤立页面：删除或补充内容使其被引用
2. 修复缺失引用：创建被引用的页面或修正链接
3. 解决矛盾观点：重写相关页面，标注来源和处理理由
4. 合并重复概念：保留更清晰的页面名，更新 aliases 和入站链接
5. 更新过时页面：重新处理相关来源
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
- 重复概念：N 个
- 低证据事实：N 个
- 缺少知识类型：N 个
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
[步骤 0] 确认 vault 路径（环境变量 $LLM_WIKI_VAULT → AGENTS.md 覆盖）
    ↓
[步骤 1] 读取 $VAULT/raw/inbox/article.md
    ↓
[步骤 2] 创建 $VAULT/wiki/sources/source-xxx.md
    ↓
[步骤 3] Knowledge Planner：决定 create / rewrite / link / conflict
    ↓
[步骤 4] Knowledge Compiler：重写受影响页面，合并新旧知识
    ↓
[步骤 5] 建立 [[wikilink]] 交叉引用
    ↓
[步骤 6] 更新 $VAULT/wiki/index.md
    ↓
[步骤 7] 记录 $VAULT/log.md
    ↓
[步骤 8] mv $VAULT/raw/inbox/ → $VAULT/raw/processed/
    ↓
完成，告知用户处理结果
```

## 重要原则

1. **重编译而非追加**：更新页面时重写知识结构，合并重复内容，不盲目把新段落堆到底部
2. **保留有价值旧内容**：旧内容仍正确就保留，过时内容要标注 obsolete 或移入历史语境
3. **标注来源**：每个重要观点都要追溯来源，并尽量写明证据质量
4. **标注矛盾**：发现矛盾要明确列出双方来源、时间、置信度和处理理由
5. **区分事实和推测**：低置信度内容放入未验证假设或开放问题
6. **保持简洁**：摘要页聚焦核心观点，不过度展开
7. **wikilink 优先**：使用 Obsidian 的 `[[wikilink]]` 格式
8. **移动而非删除**：处理后移动到 `$VAULT/raw/processed/`，保留原始资料

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
