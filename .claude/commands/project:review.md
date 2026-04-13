# Workspace Review Checklist

Run this complete checklist against all changed files. Every item must pass.
Do NOT suggest a commit until all categories report PASS.

Review the actual changes — read every changed file, verify correctness.

## Hooks (when applicable)

- [ ] Hook shell command tested standalone before adding to settings
- [ ] Hook fires on the correct event (PreToolUse or PostToolUse)
- [ ] Hook matcher targets the right tools (Edit, Write, Bash, etc.)
- [ ] Blocking hooks exit non-zero with a clear, actionable message
- [ ] Warning hooks exit zero and print an informational message
- [ ] Hook does NOT fire on legitimate operations (false positive test)
- [ ] Hook fails gracefully when preconditions aren't met (not a git repo, tool not installed)
- [ ] Hook command is portable (no hardcoded paths beyond repo roots)

## Settings (when applicable)

- [ ] JSON is valid (parseable)
- [ ] Permissions use glob patterns where possible (not one-off approvals)
- [ ] No overly broad permissions (`Bash(*)` is never acceptable)
- [ ] No security-sensitive permissions added without justification
- [ ] Permissions cover all tools needed by the repo's workflow
- [ ] No duplicate or redundant permission entries

## Skills (when applicable)

- [ ] Skill follows the project's existing phase structure (Setup → Assess → Plan → Implement → Verify → Wrap Up)
- [ ] Skill uses `gh issue view` to load issues (not hardcoded content)
- [ ] Skill has clear stop-and-ask points for architectural decisions
- [ ] Skill references the correct repo paths and conventions
- [ ] Skill does not duplicate functionality of existing skills
- [ ] Skill markdown renders correctly (headings, code blocks, tables)

## CLAUDE.md (when applicable)

- [ ] New rules don't conflict with individual repo CLAUDE.md files
- [ ] Cross-project rules reference their source ("per pfm-go CLAUDE.md: ...")
- [ ] No duplication of repo-specific conventions
- [ ] Formatting is consistent with existing sections

## Memory (when applicable)

- [ ] Memory file has correct frontmatter (name, description, type)
- [ ] Memory content is not derivable from code or git history
- [ ] No duplicate memories (check MEMORY.md index first)
- [ ] MEMORY.md index entry is under 150 characters
- [ ] MEMORY.md total length is under 200 lines
- [ ] Memory does not contain ephemeral state (current branch, in-progress work)

## Cross-Project Consistency

- [ ] Changes in pfm-go follow pfm-go CLAUDE.md conventions
- [ ] Changes in pfm-ui-react follow pfm-ui-react CLAUDE.md conventions
- [ ] No file edits on `main` in any repo
- [ ] Conventional Commits format used in all repos
- [ ] Workspace issue number referenced in all commits (`refs fzambone/pfm-workspace#N`)

## Final Verification

- [ ] All acceptance criteria from the workspace issue are COVERED
- [ ] Target repo CI gates pass (if target repos were modified)
- [ ] No unintended changes in any repo (`git status` is clean except staged files)

---

**Report format:** List each applicable category as PASS, FAIL, or N/A.
For failures, state the specific violation and the file:line where it occurs.
Do NOT suggest committing until every applicable category passes.

Categories:
1. Hooks
2. Settings
3. Skills
4. CLAUDE.md
5. Memory
6. Cross-Project Consistency
7. Final Verification
