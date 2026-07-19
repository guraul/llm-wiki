# ADR-001: Obsidian Vault 访问策略

- **状态**: Accepted
- **日期**: 2026-07-19
- **决策者**: gubin
- **关联**: `opencode/SKILL.md`, `~/.workbuddy/skills/llm-wiki/SKILL.md`

## 上下文

LLM Wiki skill 需要读写 Obsidian vault 来执行 ingest / query / lint 三类核心操作。
Obsidian vault 有多种访问方式可选，需要确定一个标准的"事实接口"。

候选方案：

| 方案 | 说明 | 依赖 |
|------|------|------|
| **直接文件系统读写** | 把 vault 当作普通 Markdown 文件夹 | 零 |
| **Obsidian 插件 API** | 在 app 内部运行的 JS API | Obsidian app + 插件宿主 |
| **Local REST API 插件** | 社区插件，本地起 HTTP server | Obsidian app 运行 + 装插件 + token/cert |
| **第三方 CLI / URI scheme** | `obsidian://open?vault=...&file=...` | 系统级 URI scheme |
| **Obsidian MCP server** | 包装上述任一方案的 MCP 接口 | 视实现而定 |

关键事实：

1. Obsidian 官方没有外部 REST API。仓库 `obsidianmd/obsidian-api` 是**插件 API** 类型定义，只在 app 内部可用。
2. Local REST API / REST and MCP server 等都是**社区插件**，需要 Obsidian desktop 运行 + 手动启用 + 配置认证。
3. URI scheme (`obsidian://`) 只能"打开"文件，不能读写内容。
4. Obsidian 的设计哲学是 **"vault = 普通 Markdown 文件夹"**。所有数据（frontmatter、wikilink、embeds、tags）都直接存储在 `.md` 文件内。Obsidian app 本身只是查看器 + 索引器，关闭后 `.md` 文件即为完整事实源。

## 决策

LLM Wiki 使用 **直接文件系统访问** 作为 vault 的标准接口。

Obsidian API / REST / CLI / MCP 集成是 **可选的 UX 适配器**，不作为 ingest / query / lint 核心流程的依赖。

英文版结论（便于外部引用）：

> Core knowledge operations use direct filesystem access to the Obsidian vault.
> Obsidian API, URI, REST, or plugin integrations are optional UX adapters only.

## 架构分层

```text
Core (必需，零外部依赖):
  - filesystem markdown read/write
  - rg / MCP search_wiki 全文搜索
  - frontmatter parser (YAML)
  - wikilink parser ([[xxx]] / ![[xxx]] / [[xxx|alias]] / [[xxx#heading]])

Optional UX Adapters (按需启用，不进核心):

  1. 跳转层 (zero-dep, 推荐默认启用):
     - obsidian://open?vault=...&file=...
     - 仅触发 UI 跳转，不读写内容
     - 系统 URI scheme，无插件依赖

  2. 同步层 (需 Obsidian 运行):
     - Local REST API 插件
     - 可触发命令、刷新视图、双向通知
     - 适用于"LLM 改完立刻在 Obsidian 弹出"

  3. 查询层 (需 Obsidian 运行):
     - REST/MCP 插件读取 backlinks / outline / tags
     - 适用于需要 Obsidian 派生元数据的场景
     - 注意：底层仍是 .md 文件，rg + 解析可替代大部分能力
```

## 安全写入规则

核心层直接读写文件，必须遵守以下规则，避免数据损坏和不可审查的改动：

### 1. frontmatter 必须用 YAML parser

- **禁止**用字符串替换、正则匹配等方式修改 frontmatter
- 必须用 YAML parser（如 Python `python-frontmatter`、Node `gray-matter`）读取 → 修改 → 写回
- 这样能保证 YAML 结构正确，避免缩进、引号、转义等细节问题

### 2. 写入前保留原文

- 修改已有页面前，先读取完整旧内容（在内存中保留）
- 如果改动较大，建议先 `cp` 备份到临时文件（如 `.bak`）
- 这样写入失败时可以回滚

### 3. 尽量 atomic write

- 写入新内容时，先写到临时文件（如 `xxx.md.tmp`），再 `mv` 替换原文件
- `mv` 在同一文件系统上是原子操作，能避免"写一半中断"导致的数据损坏
- 示例：
  ```bash
  write to "$VAULT/wiki/concepts/xxx.md.tmp"
  mv "$VAULT/wiki/concepts/xxx.md.tmp" "$VAULT/wiki/concepts/xxx.md"
  ```

### 4. 保证 git diff 可审查

- 单次改动粒度可控：一次 ingest 只改相关页面，不要顺手批量重写无关页面
- 改动后 `git diff` 应该是清晰的"新增/修改/删除"行，不是大段重排
- 如果某次改动 diff 超过 ~200 行，考虑拆成多次小改动
- 这样人工 review、回滚、bisect 都更容易

## 理由

1. **符合 Obsidian 设计哲学**：vault 就是文件夹，直接读写是正统做法而非绕路。
2. **零依赖**：不需要装插件、不需要 Obsidian 运行、不需要 token/cert。
3. **批量操作高效**：ingest 一次可能涉及 10-15 个页面读写，文件系统操作远快于 HTTP API 调用。
4. **git 友好**：所有改动天然可 diff、可回滚、可版本化。
5. **调试透明**：直接看文件，不需要抓 HTTP 包或读插件日志。
6. **与 Obsidian 升级解耦**：Obsidian 大版本升级时核心流程不受影响。
7. **离线可用**：在无 Obsidian 环境（CI、远程服务器、容器）中也能运行。

## 后果

### 正面

- 核心流程稳定，不依赖任何外部运行时
- 批量 ingest/rewrite 性能可控
- 与 git、CI、自动化管道天然兼容
- 跨平台一致（macOS / Linux / WSL 行为相同）

### 负面

- 不触发 Obsidian UI 事件（不会自动打开刚创建的页面）
- Dataview 等插件的实时索引会延迟到下次 Obsidian 激活时刷新
- 不能直接复用 Obsidian 内置搜索语法（但 `rg` + MCP `search_wiki` 更灵活）
- backlinks 等派生关系需要自己解析（但 wikilink parser 已可覆盖大部分）

### 缓解措施

- 跳转层默认启用 `obsidian://open` URI，让用户能在 LLM 操作后一键打开结果
- 若某场景确实需要 Dataview 实时索引，再考虑同步层作为可选项
- backlinks 解析已纳入 Core 的 wikilink parser 范畴

## 备选方案

### A. 核心改为 Local REST API 调用 — 否决

- 依赖 Obsidian app 持续运行
- 批量操作受 HTTP IPC 开销限制
- 引入 token / 自签证书配置成本
- 底层仍是读写 .md，未获取到额外"独占数据"
- 离线 / CI 场景不可用

### B. 核心改为第三方 CLI / URI scheme — 否决

- URI scheme 只能"打开"，不能读写内容
- 第三方 CLI 维护不确定，功能边界模糊
- 对 LLM 知识管理场景几乎无用

### C. 混合：核心用文件 + 通知层用 API — 当前决策

- 核心保持文件系统读写
- UX 适配器按需启用，不影响核心
- 既能保持简洁底座，又能在需要时获得 UI 集成能力

## 何时重新评估

满足以下任一条件时，重新审视本决策：

1. **Obsidian 官方推出真正的外部 REST API**（非插件 API）
2. **工作流需要实时双向同步**（如 Obsidian 内编辑立即触发 LLM 重编译）
3. **Dataview / Graph 等派生索引成为性能瓶颈**，文件系统解析已不够用
4. **需要跨设备协同编辑**，且单机文件同步不再够用
5. **Obsidian 开始把元数据持久化到非 .md 存储**（如 SQLite），破坏"vault = 文件夹"前提

## 参考

- Obsidian 官方插件 API: https://github.com/obsidianmd/obsidian-api
- Local REST API 插件: https://community.obsidian.md/plugins/obsidian-local-rest-api
- REST and MCP server 插件: https://community.obsidian.md/plugins/cli-rest-mcp
- 本项目 SKILL: `opencode/SKILL.md`
