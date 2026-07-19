# LLM Wiki Prompt Pipeline

This document records the intended prompt architecture for `llm-wiki`.
The skill should behave like a small knowledge compiler, not like a note appender.

## Design Goal

Each new source should update the durable wiki model:

```text
Raw document
  -> Source summary
  -> Knowledge planner
  -> Knowledge compiler
  -> Link update
  -> Wiki rewrite
```

The important shift is:

```text
old page + new paragraph
```

becomes:

```text
old knowledge model + new evidence -> rewritten knowledge model
```

## Pipeline

### 1. Read

Read the raw file and produce a compact source summary. The raw file remains the immutable evidence record; the source summary is the first wiki artifact.

Output:

- title
- source metadata
- core claims
- useful quotes or anchors
- evidence quality

### 2. Plan

Before writing concept or entity pages, inspect existing wiki structure and decide what should change.

The planner should produce:

- pages to create
- pages to rewrite
- pages to link
- possible duplicate pages
- contradictions
- open questions

This stage reduces page sprawl and prevents near-duplicate concepts.

### 3. Compile

The compiler creates or rewrites durable pages. It must classify knowledge by type:

| Type | Purpose |
|------|---------|
| `concept` | Abstract ideas, principles, technical concepts |
| `entity` | Tools, projects, products, people, organizations |
| `decision` | Why one option was chosen over another |
| `pattern` | Reusable solution or workflow |
| `problem` | Limitation, risk, failure mode, open issue |
| `procedure` | Steps, migration flow, operational checklist |
| `reference` | Stable facts, parameters, API details, commands |

For existing pages, the compiler must read the old page and rewrite it with the new evidence. It should not blindly append.

### 4. Link

Links are part of the knowledge model. The compiler should add wikilinks for:

- prerequisite relationships
- alternatives
- obsolete/current version relationships
- problem -> solution relationships
- decision -> evidence relationships
- pattern -> procedure relationships

### 5. Verify

After ingest, verify that:

- the source summary exists
- changed pages reference the new source
- `index.md` includes new pages
- `log.md` records the operation
- the raw file moved from `raw/inbox/` to `raw/processed/`

## Rewrite Policy

When updating an existing page:

1. Keep old content that is still correct and useful.
2. Merge duplicate facts.
3. Move new facts into the right section.
4. Mark obsolete information instead of silently deleting important history.
5. Put contradictions in `## Conflicts`.
6. Put weak evidence in `## Unverified assumptions`.
7. Update `sources`, `evidence`, `confidence`, and `updated`.

## Confidence Policy

Use confidence to avoid compiling guesses into facts:

| Level | Evidence |
|-------|----------|
| `high` | Official documentation, source code, architecture decision records, primary sources |
| `medium` | Trusted articles, team notes, multiple sources that agree |
| `low` | Single user note, incomplete source, speculation, inferred synthesis |

Low-confidence claims can be useful, but they should be labeled as assumptions or open questions.

## Future Refactor

`opencode/SKILL.md` can later be split into smaller files:

```text
skills/
  core.md
  ingest.md
  compiler.md
  query.md
  lint.md
```

That split is useful once the skill grows further. For now, keeping one installable `SKILL.md` is simpler.
