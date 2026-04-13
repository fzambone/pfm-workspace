# Ship a Workspace Issue

Commit, push, create PRs, merge, and close the workspace issue. This skill handles both
workspace-only changes and changes that span target repos (pfm-go, pfm-ui-react).

Run this skill **after verification passes** (`/project:implement` Phase 5).

---

## Preconditions

- All verification gates must have passed in this session
- No uncommitted changes that belong to a different story
- For target repo changes: must be on a `feat/` branch in each target repo
- For workspace changes: must be on a `feat/` branch in pfm-workspace

If any precondition fails, stop and report what needs to be resolved first.

---

## Step 1 — Business Alignment Review

Before committing, verify we built the **right thing**:

- **Scope fidelity:** Does the implementation match what the workspace issue asked for?
- **Acceptance criteria:** Is every criterion in the issue body fully addressed?
- **No collateral damage:** Do existing workflows in target repos still work?

Report the verdict:
```
Business Alignment: PASS / NEEDS DISCUSSION
- [criterion 1] → addressed / not addressed
- ...
```

If NEEDS DISCUSSION, stop and ask before proceeding.

---

## Step 2 — Stage and commit per repo

For EACH repo that has changes (may be 1, 2, or 3 repos):

### 2.1 Stage files

```
cd <repo-path>
git status
git add <file1> <file2> ...
```

Exclude:
- `.claude/plans/` — session artifacts
- Binary files, build artifacts, coverage output

Verify: `git diff --cached --stat`

### 2.2 Commit

Use Conventional Commits format. Reference the **workspace** issue number:

```
git commit -m "$(cat <<'EOF'
type(scope): imperative description

- Bullet per meaningful change (what and why, not how)

refs fzambone/pfm-workspace#N
EOF
)"
```

Rules:
- `type`: `feat`, `fix`, `refactor`, `chore`, `docs`
- `scope`: the concern area (e.g. `hooks`, `settings`, `skills`, `review`)
- For target repo commits, use `refs fzambone/pfm-workspace#N` (not `closes`)
- Only the workspace repo commit (or the last repo if no workspace changes) uses `closes #N`

---

## Step 3 — Push per repo

For each repo with changes:
```
cd <repo-path>
git push -u origin <branch-name>
```

---

## Step 4 — Create Pull Requests

For each repo with changes, create a PR:

```
gh pr create --title "<type>(scope): description" --body "$(cat <<'EOF'
## Summary
- bullet 1
- bullet 2

## Workspace Issue
Implements fzambone/pfm-workspace#N

## Verification
- [ ] Acceptance criteria: PASS
- [ ] Target repo CI gate: PASS (or N/A)
- [ ] `/project:review`: PASS
EOF
)"
```

---

## Step 5 — Merge PRs

Merge in order: **target repos first, then workspace** (if workspace has changes).

```
gh pr merge --squash --delete-branch
```

Confirm each PR number before merging.

---

## Step 6 — Sync main in all repos

For each repo that had changes:
```
cd <repo-path>
git checkout main
git pull
```

---

## Step 7 — Close the workspace issue (if not auto-closed)

If the workspace issue is still open (e.g., only `refs` were used in commits):
```
gh issue close <N> --comment "Implemented across repos. See linked PRs."
```

---

## Step 8 — Report

```
Workspace Issue:  #<N> — <title>
Repos changed:    <list>

Per-repo PRs:
  pfm-go:         #<number> — <url> (merged ✓ / N/A)
  pfm-ui-react:   #<number> — <url> (merged ✓ / N/A)
  pfm-workspace:  #<number> — <url> (merged ✓ / N/A)

Workspace issue:  closed ✓
All repos:        main synced ✓
Business:         PASS

Issue #<N> is done.
```
