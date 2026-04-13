# Implement a Workspace Issue

Implement a GitHub issue from the pfm-workspace repo. These issues track cross-cutting work
that typically targets pfm-go, pfm-ui-react, or both. This skill loads the issue, determines
where the work happens, and orchestrates implementation across repos.

Run this skill at the **start of every workspace issue**. Do not begin implementation without it.

---

## Phase 1 — Setup

### 1.1 Identify the issue

- Read the argument passed to this skill (e.g. `/project:implement 2`)
- If no argument, check the current branch name for a numeric suffix
- If still not found, ask: "Which pfm-workspace issue should I implement?"

### 1.2 Load the issue

```
gh issue view <N>
```

Read the full issue body carefully. Extract:
- The stated **goal** — what problem this solves
- Explicit **acceptance criteria** (checklist items in the issue body)
- Implicit requirements in prose
- Explicitly **out-of-scope** items
- **Depends On** — verify all dependencies are closed
- **Target repo(s)** — determine from the issue body which repo(s) need changes

### 1.3 Classify the work

Determine the work type from the issue content:

| Type | Where changes happen | Branch strategy |
|---|---|---|
| **Single-repo config** | pfm-go OR pfm-ui-react | Branch in the target repo |
| **Both-repo config** | pfm-go AND pfm-ui-react | Branch in each target repo |
| **Workspace-only** | pfm-workspace | Branch in pfm-workspace |
| **Skill creation** | pfm-workspace and/or target repos | Branch where the skill lives |

### 1.4 Create branches

For **target repo work** (hooks, settings, review changes):
```
cd <target-repo-path>
git checkout main && git pull
git checkout -b feat/<scope>-<description>-ws<N>
```

Where `ws<N>` indicates the workspace issue number (e.g., `feat/hooks-branch-guard-ws3`).

For **workspace-only work** (skills, CLAUDE.md):
```
cd /Users/fzambone/projects/pfm-workspace
git checkout main && git pull
git checkout -b feat/<scope>-<description>-<N>
```

### 1.5 Repo paths

| Repo | Path |
|---|---|
| pfm-go | `/Users/fzambone/projects/go/pfm-go` |
| pfm-ui-react | `/Users/fzambone/projects/pfm-ui-react` |
| pfm-workspace | `/Users/fzambone/projects/pfm-workspace` |

---

## Phase 2 — Codebase Assessment

Explore the relevant files before making changes:

**For hooks/settings issues:**
- Read the target repo's `.claude/settings.local.json`
- Read the target repo's `.claude/CLAUDE.md` for workflow rules
- Check if any hooks already exist
- Understand the permission patterns in use

**For skill issues:**
- Read the target repo's existing skills in `.claude/commands/`
- Read the target repo's `CLAUDE.md` for conventions the skill must enforce
- Check for patterns in existing skills (structure, phases, gates)

**For cross-project issues:**
- Read both repos' CLAUDE.md files
- Read the workspace CLAUDE.md
- Understand the API contract (OpenAPI spec location, TypeScript type locations)

---

## Phase 3 — Implementation Plan

Write a plan to `.claude/plans/<branch-name>.md` with these sections:

```
## Summary
One paragraph: what this issue delivers and why.

## Target repo(s)
- Which repo(s) will have file changes

## Changes
- List of files to create or modify, with one-line description of each change

## Verification strategy
- How to verify each acceptance criterion
- For hooks: test scenarios (what should be blocked, what should pass through)
- For skills: dry-run scenarios
- For settings: before/after comparison

## Implementation order
1. Step 1
2. Step 2
...

## Open decisions
- List any ambiguities that require input before starting
```

**Stop here and present the plan.** Surface all open decisions. Wait for confirmation before Phase 4.

---

## Phase 4 — Implementation

### For hooks
1. Design the hook shell command — test it standalone first
2. Add the hook configuration to `.claude/settings.local.json`
3. Test the hook by simulating the trigger scenario
4. Verify the hook does NOT fire on legitimate operations

### For settings cleanup
1. Read the current settings file
2. Identify patterns and consolidate to glob wildcards
3. Write the cleaned file
4. Verify no existing workflow is broken

### For skills
1. Write the skill markdown following the repo's existing skill patterns
2. Ensure phases match the project's workflow (setup → assess → plan → implement → verify)
3. Verify the skill can be invoked with a test argument

### For CLAUDE.md changes
1. Read the current CLAUDE.md
2. Make targeted additions — never rewrite sections that work
3. Verify no conflicts with individual repo CLAUDE.md files

### For memory system
1. Read existing memories in `~/.claude/projects/-Users-fzambone-projects/memory/`
2. Create or update memory files with proper frontmatter
3. Update MEMORY.md index
4. Verify no duplicates

### Rules
- **One step at a time.** Pause at decisions.
- **Test every hook** before considering it done.
- **Respect each repo's conventions** — pfm-go rules apply in pfm-go, pfm-ui-react rules in pfm-ui-react.

---

## Phase 5 — Verification

### Gate 1 — Acceptance criteria

Cross-reference each acceptance criterion from the issue:

```
Issue #N: <title>

Requirements:
[REQ-1] <description> → COVERED / PARTIAL / MISSING
[REQ-2] <description> → COVERED / PARTIAL / MISSING
...

Verdict: PASS / FAIL
```

### Gate 2 — No regressions

For target repo changes:
- Run the target repo's CI gate (`make ci` for pfm-go, `pnpm ci` for pfm-ui-react)
- Verify existing workflows still function

For workspace changes:
- Verify skill files are valid markdown
- Verify settings JSON is valid
- Verify CLAUDE.md has no formatting issues

### Gate 3 — Review

```
/project:review
```

Run the workspace review checklist. All categories must PASS.

---

## Phase 6 — Wrap Up

Report to the user:
- Issue summary: what was implemented
- Files changed per repo (list with one-line description)
- Verification results
- Any deferred items or follow-up work

Ready for `/project:ship`.
