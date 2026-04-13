# Workspace Issue Acceptance Verification

Verify that the implementation satisfies the business requirements of the workspace issue.
Run BEFORE running `/project:review` and BEFORE committing.

## Steps

### 1. Identify the issue number

- Check branch names in all repos for a numeric suffix (e.g. `feat/hooks-branch-guard-ws3`)
- Check recent commit messages for `refs fzambone/pfm-workspace#N` patterns
- If not found, ask: "Which workspace issue does this work implement?"

### 2. Fetch the issue

```
gh issue view <N>
```

Read the full issue body. Extract:
- The stated **goal** or problem being solved
- Explicit **acceptance criteria** (checklist items)
- Implicit requirements described in prose
- Any explicitly **out-of-scope** items

### 3. Inspect the implementation

For each repo that has changes:

```
cd <repo-path>
git diff main...HEAD
git status
```

Read every changed file. Understand what was added, changed, or removed.

### 4. Cross-reference each requirement

For every requirement or acceptance criterion extracted in Step 2:

- **COVERED** — Clear evidence exists: the change is present and testable/verified
- **PARTIAL** — Change exists but verification is incomplete or edge cases are missing
- **MISSING** — No evidence of this requirement in the changes

### 5. Check for scope creep

List any changes NOT traceable to a requirement in the issue.
Flag them as JUSTIFIED or NEEDS DISCUSSION.

### 6. Report

```
Workspace Issue #N: <title>

Target repos inspected: <list>

Requirements:
[REQ-1] <description> → COVERED / PARTIAL / MISSING
[REQ-2] <description> → COVERED / PARTIAL / MISSING
...

Scope (changes not traceable to a requirement):
- <repo>:<file> — <description> [JUSTIFIED / NEEDS DISCUSSION]

Verdict: PASS / FAIL
```

**PASS** = all requirements COVERED.
**FAIL** = any requirement is MISSING or PARTIAL.

Do NOT suggest committing if verdict is FAIL.
