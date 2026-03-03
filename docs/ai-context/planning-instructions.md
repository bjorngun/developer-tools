# Planning Instructions

> **Priority: HIGH** — Read this before creating or following any multi-task plan.
> Referenced by: `.github/copilot-instructions.md` and agent files.
>
> This document is **project-independent**. All project-specific commands (test, lint, code map),
> agent rosters, and file paths come from each project's `.github/copilot-instructions.md`.

---

## Table of Contents

- [Planning Instructions](#planning-instructions)
  - [Table of Contents](#table-of-contents)
  - [When to Create a Plan](#when-to-create-a-plan)
  - [Plan File Location](#plan-file-location)
  - [Following a Plan](#following-a-plan)
    - [Before Starting a Task](#before-starting-a-task)
    - [During Execution](#during-execution)
    - [After Completing a Task](#after-completing-a-task)
    - [After Completing a Phase](#after-completing-a-phase)
  - [Task Index Format](#task-index-format)
    - [Canonical Format](#canonical-format)
    - [Column Definitions](#column-definitions)
  - [Phase Guidelines](#phase-guidelines)
    - [Why Phases?](#why-phases)
    - [Rules](#rules)
    - [Suggested Phase Pattern](#suggested-phase-pattern)
  - [Starting a Plan](#starting-a-plan)
    - [Required Plan Header](#required-plan-header)
    - [Plan Detail Sections](#plan-detail-sections)
  - [Completing a Plan (Final Phase)](#completing-a-plan-final-phase)
    - [Part 1: Extract \& Preserve Knowledge](#part-1-extract--preserve-knowledge)
      - [Changelog Entry](#changelog-entry)
    - [Part 2: Tidy Up for PR](#part-2-tidy-up-for-pr)
  - [Model Cost Guidelines](#model-cost-guidelines)
  - [Agent Assignment Guidelines](#agent-assignment-guidelines)
  - [Task Completion Checklist](#task-completion-checklist)

---

## When to Create a Plan

Create a plan document (`.md` file) when **any** of these are true:

- The work needs **more than one prompt/context window** to execute well.
- There are **3+ distinct tasks** that depend on each other or share context.
- Multiple **agents or domains** are involved.
- The work is complex enough that losing context mid-way would cause rework.

**If the work is a single, self-contained task** (one file, one concern, < 30 min), skip the plan and just do it.

---

## Plan File Location

```
docs/development-notes/{feature-name}-plan.md
```

Examples: `cli-refactor-plan.md`, `test-suite-reorganization-plan.md`, `v2-migration-plan.md`

---

## Following a Plan

> **This is the most important section.** Agents follow plans far more often than they create them. If you were directed to a plan file, read this section first.

### Before Starting a Task

- **Check the Task Index** — make sure the task isn't already done or blocked.
- **Read the detail section** for that task.
- **Check if previous phases left notes** for this task (agents add notes when they discover things relevant to future tasks).

### During Execution

- **Mark the task `🔄 In progress`** in the Task Index before starting.
- **Stay within scope** — if you discover unrelated work, add it as a new task rather than expanding the current one.
- **If you learn something useful for a future task**, add a `> 📝 Note from Task N:` callout in that future task's detail section. The agent doing that task may not have the same context.

> **External task trackers:** If your environment provides a built-in task tracking tool (e.g., `manage_todo_list`), the **plan file is the authoritative tracker**. You may use external tools for your own working memory, but all status updates MUST be reflected in the Task Index in the plan file. Do not rely on external tools as a substitute for updating the plan.

### After Completing a Task

1. **Mark the task `✅ Done`** in the Task Index immediately — not later, not in batch.
2. **Add a completion note** under the task heading with **all** of the following:
   - Date and commit hash
   - Key metrics (e.g., test count, lines saved)
   - Key decisions made and why
   - Any issues encountered
   - Notes for future tasks (if applicable)
   - **Changelog bullets** — Added/Changed/Removed/Fixed (user-facing perspective)

   > **Why so detailed?** Phases often span multiple sessions. A fresh agent assembling the phase summary will have *only* these notes to work from — not the previous session's memory. Write enough that the summary can be produced without guessing.
3. **Commit changes** with a descriptive message:
   ```bash
   git add -A
   git commit -m "refactor: Task N — short description"
   ```

### After Completing a Phase

> **This is a separate step from per-task completion notes.** Task notes are written *during* execution for the benefit of the next task. The phase summary is written *after all tasks in the phase are done*, for the benefit of future agents who open the plan and need a quick overview without reading stale detail.

1. **Run tests** using the project's test command (see `copilot-instructions.md`).
2. **Write a phase summary** — This is a **mandatory, distinct deliverable**. Do not skip it, and do not confuse it with the per-task completion notes you already wrote.

   **What to do:** Replace the detailed task sections (What/Files/Acceptance criteria) for all completed tasks in the phase with a single, condensed phase-level summary block. Keep the task headings and their completion notes — remove the original planning detail that is now stale.

   **What to include** (assemble from the per-task completion notes — not from memory):
   - What was done (per task, 1-2 lines each)
   - Key decisions made (compiled from task notes)
   - Any issues encountered (compiled from task notes)
   - Notes for future phases
   - **Changelog notes** — Compiled from per-task changelog bullets into a single phase-level list

   **Why this matters:** Future agents reading the plan see completed phases as brief summaries and uncompleted phases as full detail. This keeps the plan file lean and navigable. Without this step, the plan accumulates stale detail that wastes context window space and confuses future readers.

3. **Commit** the phase summary update:
   ```bash
   git add -A
   git commit -m "docs: Phase N summary"
   ```

> **Checklist reminder:** If you use `manage_todo_list` or similar, add an explicit "Write phase summary" item between "Run tests" and "Commit" so this step is never accidentally merged into the commit step.

---

## Task Index Format

The **Task Index MUST be at or near the top** of the plan file. Only the following may appear above it:

1. Title (`# Plan Name`)
2. Brief metadata (created date, agent, scope — max 3 lines)
3. A short overview paragraph (optional, max 5 lines)

Everything else goes **below** the Task Index.

### Canonical Format

```markdown
## Task Index

| Phase | # | Task | Details | Agent | Cost | Complexity | Est. | Refs | Status |
|-------|---|------|---------|-------|------|------------|------|------|--------|
| **0 — Setup** | 0 | Create scaffolding | [Details](#task-0-create-scaffolding) | QA Engineer | 💚 | Simple | 10 min | | |
| **1 — Core** | 1 | Implement feature X | [Details](#task-1-implement-feature-x) | (per project) | 💛 | Medium | 30 min | | |
| | 2 | Add error handling | [Details](#task-2-add-error-handling) | (per project) | 💚 | Simple | 15 min | | |
| **2 — Polish** | 3 | Write tests | [Details](#task-3-write-tests) | QA Engineer | 💛 | Medium | 25 min | | |
| **N — Cleanup** | N | Finalize & update docs | [Details](#task-n-finalize--update-docs) | Librarian | 💚 | Simple | 15 min | | |
```

### Column Definitions

| Column | Required | Description |
|--------|----------|-------------|
| **Phase** | ✅ | Group label (only shown on first row of each phase). Format: `**N — Name**` |
| **#** | ✅ | Sequential task number (0-based) |
| **Task** | ✅ | Short, action-oriented name (3-8 words) |
| **Details** | ✅ | Link to the detailed section in the same plan: `[Details](#task-n-name)` |
| **Agent** | ✅ | Which agent should execute this task |
| **Cost** | ✅ | Model cost: 💚 Low / 💛 Mid / 🔴 High (see [guidelines](#model-cost-guidelines)) |
| **Complexity** | ✅ | Simple / Medium / Complex |
| **Est.** | ✅ | Estimated time (e.g., `15 min`, `45 min`) |
| **Refs** | Optional | Links to related docs, ADRs, URLs, or plan sections that help with the task |
| **Status** | ✅ | Empty (not started) / `🔄 In progress` / `✅ Done` / `⏳ Blocked (reason)` |

---

## Phase Guidelines

### Why Phases?

Phases group contextually-related tasks so an agent can work through them in a single context window without losing track. They also create natural checkpoints for testing and committing.

### Rules

1. **Group by shared context** — Tasks within a phase should touch related files/concepts so the agent doesn't need to re-read unrelated code between tasks.
2. **Keep phases small** — Aim for **2-5 tasks per phase**. If a phase has 6+ tasks, split it. A bloated phase means the context window fills up and output quality drops.
3. **Order phases by dependency** — Earlier phases should produce outputs that later phases build on.
4. **Every plan ends with a Cleanup phase** — See [Completing a Plan](#completing-a-plan-final-phase).

### Suggested Phase Pattern

| Phase | Purpose | Typical Tasks |
|-------|---------|---------------|
| **0 — Setup** | Scaffolding, file moves, structural prep | Create directories, move files, add `__init__.py` |
| **1-N — Core work** | The actual feature/refactor work | Implementation, organized by context |
| **N-1 — Polish** | Quality pass | Tests, parametrize, lint, consolidate |
| **N — Cleanup** | Finalize for PR | Review plan, update docs, regenerate code map, commit |

---

## Starting a Plan

When you determine a plan document is needed:

1. **Create the file** at `docs/development-notes/{feature}-plan.md`.
2. **Include the required plan header** (see [below](#required-plan-header)).
3. **Write the Task Index first** — before any detail sections. This forces you to think through the full scope.
4. **Add detail sections** below the Task Index for each task (headed `## Task N: Name`).
5. **Include a Cleanup phase as the final phase** (see [Completing a Plan](#completing-a-plan-final-phase)).
6. **Commit the plan** before starting execution:
   ```bash
   git add docs/development-notes/{feature}-plan.md
   git commit -m "docs: Add {feature} plan"
   ```

### Required Plan Header

Every plan file MUST include a **protocol line** and a **Task Index reminder**. This ensures any agent opening the file — even with zero prior context — knows how to execute it correctly.

```markdown
# {Feature} Plan

> **Protocol**: Follow [planning-instructions.md](../ai-context/planning-instructions.md#following-a-plan) for execution rules.
> **Created**: YYYY-MM-DD
> **Agent**: {Primary Agent}
> **Scope**: {Brief scope description}

---

> ⚠️ **Execution**: Update Status column before/after each task. See [Following a Plan](../ai-context/planning-instructions.md#following-a-plan).

## Task Index

| Phase | # | Task | Details | Agent | Cost | Complexity | Est. | Refs | Status |
|-------|---|------|---------|-------|------|------------|------|------|--------|
```

The key elements:
- **Protocol line**: Links directly to the execution rules. An agent seeing this knows to read the rules before starting.
- **Task Index reminder**: Placed immediately above the table as an unmissable visual cue that this table is the authoritative status tracker.

### Plan Detail Sections

**Phase headings in the plan body:** The Task Index groups tasks into phases, but the detail sections below should also have clear phase boundaries. Use a phase heading before each group of task sections:

```markdown
---

## Phase 1 — Feature A

### Task 1: Implement core logic
...

### Task 2: Write tests for feature A
...

---

## Phase 2 — Feature B

### Task 3: Refactor into sub-package
...
```

This makes phases visually distinct in the plan body, not just in the Task Index table. When a phase is completed and summarized, the phase heading remains and the task detail below it is replaced with the condensed summary.

**Each task heading** below its phase heading should include at minimum:

- **What** — What needs to happen (1-3 sentences).
- **Files** — Which files will be created/modified/deleted.
- **Acceptance criteria** — How to know it's done.

Optional but valuable:
- **Why** — Context for why this approach was chosen.
- **Risks** — What could go wrong.
- **Notes** — Anything the executing agent should know (especially if a different agent will do it).

---

## Completing a Plan (Final Phase)

The last phase of every plan is **Cleanup**. It has two parts:

### Part 1: Extract & Preserve Knowledge

Go through the entire plan and extract every informational gem — things learned, decisions made, patterns discovered, gotchas encountered. Update the appropriate existing docs:

| What You Learned | Where to Put It |
|------------------|-----------------|
| User-facing changes | `CHANGELOG.md` under `## [Unreleased]` ([Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format) |
| Architecture decisions | Project architecture docs or `docs/development-notes/` |
| Coding patterns/conventions | Project coding standards doc |
| Agent workflow learnings | Relevant agent configuration files |

#### Changelog Entry

Compile the per-phase changelog notes into a single entry under `## [Unreleased]` in `CHANGELOG.md`. Use the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) categories:

- **Added** — New features, new files, new capabilities
- **Changed** — Modifications to existing behavior
- **Removed** — Deleted files, removed features
- **Fixed** — Bug fixes

Write the entry from a **user/reviewer perspective** (what changed and why), not agent internals.

> **Release automation:** When the PR merges to `main`, the CI workflow (`.github/workflows/version.yml`) automatically moves `[Unreleased]` content into a new versioned heading (`## [X.Y.Z] - YYYY-MM-DD`), bumps the version in `pyproject.toml`, and resets `[Unreleased]` to empty. If `[Unreleased]` is empty at merge time, the workflow falls back to generating a one-line entry from the PR title. So **always write changelog notes** — they become the official release entry.

### Part 2: Tidy Up for PR

- [ ] All Task Index items are `✅ Done`
- [ ] Tests pass (use project's test command from `copilot-instructions.md`)
- [ ] Lint passes (use project's lint command from `copilot-instructions.md`)
- [ ] Code map / docs regenerated if structure changed
- [ ] `CHANGELOG.md` updated under `## [Unreleased]` (compiled from phase changelog notes)
- [ ] Documentation updated
- [ ] **Delete the plan file** — it has served its purpose; the knowledge is now in the right docs
- [ ] Final commit:
  ```bash
  git add -A
  git commit -m "docs: Complete {feature} plan — cleanup and doc updates"
  ```

---

## Model Cost Guidelines

| Cost | Icon | When to Use | Example Models |
|------|------|-------------|----------------|
| **Low** | 💚 | Simple edits, text changes, formatting, single-file changes | GPT-4o-mini, Claude Haiku, Gemini Flash |
| **Mid** | 💛 | Logic changes, multi-file edits, moderate complexity | GPT-4o, Claude Sonnet |
| **High** | 🔴 | Complex refactoring, architecture decisions, novel problems | Claude Opus, o1-preview |

Use the lowest cost model that can handle the task well. Over-specifying wastes budget; under-specifying leads to rework.

---

## Agent Assignment Guidelines

The agent assignment table is **project-specific**. Refer to your project's `.github/copilot-instructions.md` or agent configuration files for the list of available agents and their domains.

General pattern:

| Task Type | Recommended Agent | Mode |
|-----------|-------------------|------|
| Test writing, coverage | QA Engineer | 💬 |
| Linting, cleanup, formatting | Janitor | 🔄 |
| Documentation updates | Librarian | 🔄 |
| External research, sourced docs | Research Agent | 🔄 |
| Feature implementation | (project-specific agents) | 💬 |

Mode key: 💬 = interactive/chat, 🔄 = autonomous/batch

---

## Task Completion Checklist

Before marking any task `✅ Done`, verify:

- [ ] Assumptions stated explicitly
- [ ] Files touched are listed in the completion note
- [ ] Tests pass (use project's test command)
- [ ] Lint is clean (use project's lint command)
- [ ] Documentation updated if needed (Librarian rule)
- [ ] Code map regenerated if structure changed
- [ ] Risk notes provided for breaking changes
- [ ] Changes committed with descriptive message
