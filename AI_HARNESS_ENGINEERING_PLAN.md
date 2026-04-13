# AI Harness Engineering Plan — PFM Platform

**Date:** 2026-04-13
**Scope:** pfm-go (Go backend) + pfm-ui-react (React frontend)
**Author:** Claude (requested by Felipe Zambone)

---

## Executive Summary

You've built one of the most sophisticated AI-driven development workflows I've seen in a personal project. Both repos have a complete skill lifecycle (`implement` → `verify-issue` → `review` → `ship`), planning tools (`milestone`, `breakdown`), a teaching mandate, and strict TDD gates. The foundation is excellent.

This plan identifies **what's missing** and **what's possible** across five dimensions:

1. **Hooks** — Automated guardrails that enforce your workflow without manual invocation
2. **Cross-project orchestration** — Coordinating full-stack features across two repos
3. **Scheduled agents** — Autonomous background agents for recurring maintenance
4. **Claude API in the product** — AI features that make PFM smarter for you and your wife
5. **Skill refinements** — Targeted improvements to your existing skill set

Priority is ordered by **impact-to-effort ratio** — hooks and settings cleanup first (high leverage, low effort), managed agents and product AI last (high effort, transformative impact).

---

## Part 1: Current State Assessment

### What You've Built (Strong Foundation)

| Capability | pfm-go | pfm-ui-react | Quality |
|---|---|---|---|
| `/project:implement` (6-phase TDD) | Yes | Yes | Excellent — full lifecycle |
| `/project:review` (quality checklist) | 10 categories | 9 categories | Excellent — domain-specific |
| `/project:verify-issue` (acceptance) | Yes | Yes | Solid |
| `/project:ship` (commit-to-merge) | Yes | Yes | Solid |
| `/project:breakdown` (epic → issues) | Yes | Yes | Excellent — behavioral ACs |
| `/project:milestone` (conversational) | Yes | Yes | Excellent |
| `/project:learn` (teaching) | Go mastery | React/TS mastery | Great |
| `/review-tests` (TDD audit) | Yes | Yes | Solid |
| CLAUDE.md (conventions) | Comprehensive | Comprehensive | Excellent |
| .claude/CLAUDE.md (workflow) | Yes | Yes | Clear |
| CI/CD (PR + merge gates) | Yes + deploy | Yes | Production-grade |
| Settings (permissions) | Organic growth | Clean | Needs cleanup (Go) |
| Hooks | None | None | **Gap** |
| Cross-project skills | None | None | **Gap** |
| Scheduled agents | None | None | **Gap** |
| Memory system | Empty | Empty | **Gap** |
| AI features in product | None | None | **Opportunity** |

### What's Working Exceptionally Well

1. **Skill lifecycle is complete.** The `milestone → breakdown → implement → verify → review → ship` chain covers the entire story lifecycle. This is rare even in professional teams.

2. **Domain-specific review checklists.** The Go checklist (10 categories including OTel tracing, SQL conventions, Go traps) and React checklist (9 categories including a11y, Tailwind, performance) are custom-tailored, not generic.

3. **Teaching mandate is embedded in the workflow.** The CLAUDE.md files don't just describe conventions — they instruct Claude to explain Go/React idioms as it works. This turns every story into a learning session.

4. **Behavioral acceptance criteria.** Your `/project:breakdown` skill explicitly enforces "WHAT not HOW" — no code snippets in issues, no prescriptive implementation. This keeps the implementer (Claude) free to make good decisions.

5. **Hexagonal architecture + strict import rules.** Both CLAUDE.md files define clear layer boundaries with a table of what can import what. This is the kind of constraint AI works well within.

### What's Missing (Gaps to Address)

| Gap | Impact | Effort |
|---|---|---|
| No hooks for automated guardrails | High — manual enforcement is fragile | Low |
| Settings.local.json is organically grown | Medium — noisy, hard to audit | Low |
| No cross-project coordination | High — full-stack features require 2 sessions | Medium |
| No scheduled agents for maintenance | Medium — manual dependency/quality checks | Medium |
| No memory across sessions | Medium — context is lost between sessions | Low |
| No AI features in the product | High — the product itself would benefit | High |
| Skills are duplicated across repos | Low — they're similar but maintained separately | Medium |

---

## Part 2: Hooks — Automated Guardrails

Hooks are shell commands that Claude Code executes automatically in response to events. They're configured in `.claude/settings.json` (or `.claude/settings.local.json` for local-only) under the `hooks` key.

### Available Hook Events

| Event | When It Fires | Use Case |
|---|---|---|
| `PreToolUse` | Before a tool runs | Block dangerous operations, enforce conventions |
| `PostToolUse` | After a tool completes | Capture output, trigger follow-up actions |
| `Notification` | When Claude wants to notify | Custom notification routing |
| `Stop` | When Claude finishes a turn | Post-turn validation, summary generation |

### Recommended Hooks

#### Hook 1: Branch Guard (Both Projects)

**Purpose:** Prevent any file edits on `main` — enforce your "branch before coding" rule automatically.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "command": "branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null); if [ \"$branch\" = \"main\" ]; then echo 'BLOCKED: Create a feature branch before editing files. Run: git checkout -b feat/<scope>-<description>-<N>'; exit 1; fi"
      }
    ]
  }
}
```

**Why:** Your `.claude/CLAUDE.md` says "No edits on main — ever" but this is currently enforced only by skill instructions. A hook makes it impossible to bypass.

#### Hook 2: Lint-on-Save (Both Projects)

**Purpose:** Run the relevant linter after every file write to catch issues immediately rather than at the CI gate.

For pfm-go:
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "command": "if echo \"$TOOL_INPUT\" | grep -q '\\.go\"'; then golangci-lint run --fast $(echo \"$TOOL_INPUT\" | grep -o '\"[^\"]*\\.go\"' | tr -d '\"') 2>&1 | head -20; fi"
      }
    ]
  }
}
```

For pfm-ui-react:
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "command": "if echo \"$TOOL_INPUT\" | grep -qE '\\.(ts|tsx)\"'; then pnpm eslint $(echo \"$TOOL_INPUT\" | grep -oE '\"[^\"]*\\.(ts|tsx)\"' | tr -d '\"') 2>&1 | head -20; fi"
      }
    ]
  }
}
```

**Why:** Catches lint errors at write-time rather than during `make ci` / `pnpm ci`. Reduces the feedback loop from minutes to seconds.

#### Hook 3: Import Rule Enforcer (pfm-go)

**Purpose:** Automatically verify that domain packages don't import adapter/platform packages — your most critical architectural constraint.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "command": "if echo \"$TOOL_INPUT\" | grep -q 'internal/domain/'; then file=$(echo \"$TOOL_INPUT\" | grep -o '\"[^\"]*internal/domain/[^\"]*\\.go\"' | tr -d '\"'); if [ -n \"$file\" ] && grep -qE '\"github.com/zambone/pfm-go/internal/(adapter|platform|middleware)' \"$file\" 2>/dev/null; then echo \"BLOCKED: Domain package imports adapter/platform/middleware. Hexagonal architecture violation.\"; exit 1; fi; fi"
      }
    ]
  }
}
```

**Why:** This is your "#1 Non-Negotiable" — domain layer has zero knowledge of infrastructure. Currently enforced only by code review. A hook catches it at write-time.

#### Hook 4: Test File Existence Guard (Both Projects)

**Purpose:** When writing a production file, warn if no corresponding test file exists — enforces TDD discipline.

For pfm-go:
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "command": "file=$(echo \"$TOOL_INPUT\" | grep -o '\"[^\"]*\\.go\"' | tr -d '\"'); if [ -n \"$file\" ] && echo \"$file\" | grep -qv '_test\\.go$' && echo \"$file\" | grep -q 'internal/'; then testfile=\"${file%.go}_test.go\"; if [ ! -f \"$testfile\" ]; then echo \"WARNING: No test file at $testfile. TDD requires a failing test BEFORE production code.\"; fi; fi"
      }
    ]
  }
}
```

**Why:** Your TDD rule says "NEVER write production code before a failing test." This hook makes the rule visible even outside the `/project:implement` workflow.

### Hook Implementation Priority

1. Branch Guard — immediate, protects against the highest-risk mistake
2. Import Rule Enforcer — immediate, protects architectural integrity
3. Test File Existence Guard — soon, reinforces TDD discipline
4. Lint-on-Save — nice-to-have, reduces feedback loop

---

## Part 3: Settings Cleanup

### Problem

The pfm-go `settings.local.json` has 112 lines of organically-accumulated permissions. Many are one-off approvals from past sessions (e.g., specific `sed` commands, exact `docker` socket paths, `echo` commands). This makes it hard to audit what's actually allowed and creates noise.

### Recommended Cleanup

Replace the sprawling permission list with glob patterns:

```json
{
  "permissions": {
    "allow": [
      "Bash(git:*)",
      "Bash(go:*)",
      "Bash(make:*)",
      "Bash(golangci-lint:*)",
      "Bash(goose:*)",
      "Bash(sqlc:*)",
      "Bash(gh:*)",
      "Bash(fly:*)",
      "Bash(govulncheck:*)",
      "Bash(swag:*)",
      "Bash(curl:*)",
      "Bash(ls:*)",
      "Bash(grep:*)",
      "Bash(python3:*)",
      "Bash(docker:*)",
      "Bash(podman:*)",
      "Bash(TESTCONTAINERS_RYUK_DISABLED=true:*)",
      "Bash(DOCKER_HOST=*:*)",
      "WebFetch(domain:raw.githubusercontent.com)",
      "WebFetch(domain:pfm-go-api.fly.dev)",
      "WebFetch(domain:pfm-go-api.zambone.dev)",
      "WebSearch",
      "Read(//Users/fzambone/projects/go/pfm-go/**)",
      "Read(//Users/fzambone/**)"
    ]
  }
}
```

This reduces 112 lines to ~24, covers all the same use cases, and is auditable at a glance. The pfm-ui-react settings are already clean — just verify they're complete.

---

## Part 4: Cross-Project Orchestration

### The Problem

When you implement a full-stack feature (e.g., "add household listing"), you currently need:
1. One Claude Code session in pfm-go to implement the API endpoint
2. A separate Claude Code session in pfm-ui-react to build the UI
3. Manual coordination to ensure the frontend matches the backend API contract

This is the biggest workflow gap. There's no skill that spans both repos.

### Strategy: Shared Skills + API Contract Verification

#### Option A: Workspace-Level Skills (Recommended)

Create a parent directory with shared skills that reference both projects:

```
/Users/fzambone/projects/
  pfm-workspace/                 ← NEW: workspace-level orchestration
    .claude/
      CLAUDE.md                  ← Cross-project context and rules
      commands/
        project:full-stack.md    ← Full-stack feature implementation
        project:api-sync.md      ← API contract verification
        project:release.md       ← Coordinated release
    CLAUDE.md                    ← Workspace identity
  go/pfm-go/                    ← existing
  pfm-ui-react/                 ← existing
```

When you open Claude Code from `pfm-workspace/`, you have access to both projects and the cross-project skills.

#### Skill: `/project:full-stack` (New)

A skill that orchestrates implementing a feature across both repos:

```
Phase 1 — Load the issue and identify which layers are affected
Phase 2 — Backend first: implement API endpoint in pfm-go (using pfm-go's conventions)
Phase 3 — Generate/update TypeScript types from the OpenAPI spec
Phase 4 — Frontend: implement UI in pfm-ui-react (using pfm-ui-react's conventions)
Phase 5 — Integration verification: start both services, test end-to-end
Phase 6 — Ship both: create PRs in both repos, link them
```

#### Skill: `/project:api-sync` (New)

Fetches the OpenAPI spec from pfm-go and verifies that pfm-ui-react's TypeScript types match:

```
1. Fetch /api/v1/openapi.yaml from the backend
2. Parse all endpoint request/response shapes
3. Compare against TypeScript types in src/features/*/types.ts
4. Report: MATCH / DRIFT / MISSING for each endpoint
5. Optionally generate updated TypeScript types
```

**This is high-value** because your backend already generates an OpenAPI spec (via swag) and your frontend's CLAUDE.md already says "fetch openapi.yaml first" before implementing API calls. Automating this closes the loop.

#### Skill: `/project:release` (New)

Coordinates deployment:
```
1. Verify both repos are on main with clean status
2. Run CI gates in both repos
3. Deploy backend first (fly deploy)
4. Smoke test backend health
5. Deploy frontend (when frontend deployment is set up)
6. End-to-end verification
```

#### Option B: Git Submodules (Not Recommended)

Putting both repos as submodules would let Claude Code see them in one tree, but it adds git complexity. The workspace approach in Option A is simpler and more maintainable.

---

## Part 5: Scheduled Agents (Remote Triggers)

Claude Code supports scheduled agents via `CronCreate` — these run on a cron expression without requiring an interactive session. They're ideal for recurring maintenance that shouldn't interrupt your development flow.

### Recommended Scheduled Agents

#### Agent 1: Nightly Quality Sentinel

**Schedule:** Every night at 2 AM
**What it does:**
1. Pull latest main in both repos
2. Run `make ci` (pfm-go) and `pnpm ci` (pfm-ui-react)
3. Run `/project:review` against the current main
4. If any category FAILs, open a GitHub issue with the violations
5. Check for known vulnerability advisories (`govulncheck`, `pnpm audit`)

**Why:** Catches regressions that slip through PR reviews. Also catches dependency vulnerabilities before they become critical.

#### Agent 2: Weekly Dependency Health Check

**Schedule:** Every Monday at 8 AM
**What it does:**
1. Check for outdated dependencies (`go list -m -u all`, `pnpm outdated`)
2. Check for security advisories
3. If critical updates exist, open a GitHub issue with the update plan
4. Optionally create a branch and PR with the updates

**Why:** You pin dependency versions (good), but this means you need to actively monitor for updates. A weekly agent handles this without manual checking.

#### Agent 3: API Contract Drift Detector

**Schedule:** After every pfm-go deployment (triggered via GitHub Actions webhook → RemoteTrigger)
**What it does:**
1. Fetch the live OpenAPI spec from pfm-go-api.zambone.dev
2. Compare against the TypeScript types in pfm-ui-react
3. If drift is detected, open an issue in pfm-ui-react

**Why:** When you deploy a backend change, the frontend may need to update. This catches it automatically.

#### Agent 4: Coverage Trend Tracker

**Schedule:** Weekly
**What it does:**
1. Run coverage in both repos
2. Compare against previous week's numbers (stored in a tracking file)
3. If coverage dropped below threshold, open an issue
4. Generate a simple trend report

**Why:** Your CLAUDE.md defines 70-80% thresholds, but there's no trend tracking. This prevents gradual erosion.

### Implementation Note

Scheduled agents require Claude Code to be running or accessible via the Claude remote execution infrastructure. If you're on Claude Max or Teams, these can run as remote triggers. If you're on the CLI-only plan, you can achieve similar results with GitHub Actions that invoke Claude Code in CI.

**GitHub Actions alternative:**

```yaml
# .github/workflows/nightly-sentinel.yml
name: Nightly Quality Sentinel
on:
  schedule:
    - cron: '0 2 * * *'
jobs:
  sentinel:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: anthropics/claude-code-action@v1
        with:
          prompt: |
            Run the full code review checklist against the current main branch.
            Report any category that FAILs. Open a GitHub issue if violations found.
```

This is the pragmatic path if managed agents aren't available on your plan yet.

---

## Part 6: Claude Managed Agents Platform

### What Are Managed Agents?

Claude's managed agents (accessible via the Anthropic API) are autonomous agents that can be deployed as persistent services. They differ from Claude Code skills in that they:

- Run server-side, not in your terminal
- Can be triggered by webhooks, schedules, or API calls
- Have persistent state across invocations
- Can integrate with external services (Slack, GitHub, email)

### Where Managed Agents Fit Your Setup

For your current scale (2 repos, personal/family use), managed agents are **not the highest priority**. Your Claude Code skills already handle the development workflow effectively. However, there are two compelling use cases:

#### Use Case 1: PFM AI Assistant (Product Feature)

Instead of embedding Claude API calls directly in pfm-go, deploy a managed agent that:
- Has access to your PFM database (read-only)
- Can answer natural language questions about your finances
- Runs as a separate service called by pfm-go when the user asks a question

**Architecture:**
```
User → pfm-ui-react → pfm-go → Claude Managed Agent
                                  ↓
                              Tool: query_transactions(filters)
                              Tool: get_account_balances()
                              Tool: get_spending_by_category(period)
                                  ↓
                              Natural language response
```

This keeps the AI logic out of your core Go codebase (respecting hexagonal architecture) and lets the managed agent evolve independently.

#### Use Case 2: Development Orchestrator

A managed agent that acts as your "project manager":
- Monitors GitHub issues across both repos
- Suggests which issue to work on next based on dependencies
- Generates weekly progress reports
- Can be queried via Slack: "What's the status of M15?"

**When to pursue this:** After you've completed the core PFM features (households, accounts, transactions, ledger) and want to add AI intelligence to the product itself.

### Recommendation

**Now:** Focus on hooks, settings cleanup, and cross-project skills (Parts 2-4). These have the highest impact-to-effort ratio.

**Next quarter:** Set up scheduled agents for maintenance automation (Part 5).

**When product features are complete:** Evaluate managed agents for the PFM AI Assistant use case (Part 6).

---

## Part 7: Claude API Integration in the Product

This is the most transformative opportunity but also the highest effort. Here's what's possible and how it fits your architecture.

### Opportunity Assessment

| Feature | Value for You | Complexity | Priority |
|---|---|---|---|
| Transaction auto-categorization | High — manual categorization is tedious | Medium | 1st |
| Spending insights / summaries | High — natural language understanding of spending | Medium | 2nd |
| Smart search (NL queries) | Medium — "how much did we spend on groceries in March?" | Medium | 3rd |
| Budget assistant | Medium — NL budget creation and tracking | High | 4th |
| Financial health report | Nice-to-have — periodic AI-generated reports | Low | Later |

### Architecture Fit

Your hexagonal architecture is perfectly suited for this. The AI would be another **adapter**:

```
internal/
  adapter/
    ai/                    ← NEW: AI adapter
      claude_categorizer.go    ← Implements domain port
      claude_insights.go
    postgres/              ← existing
    http/                  ← existing
    auth/                  ← existing
  domain/
    ledger/
      categorizer.go       ← NEW: port interface
        type Categorizer interface {
            CategorizeTransaction(ctx, description string, amount int64) (Category, float64, error)
        }
    insights/              ← NEW: domain package
      insights.go
        type InsightGenerator interface {
            GenerateSpendingSummary(ctx, householdID uuid.UUID, period Period) (Summary, error)
        }
```

The domain defines the port (what it needs), the AI adapter implements it using Claude's API. This follows your existing pattern perfectly — domain has zero knowledge of Claude, just like it has zero knowledge of PostgreSQL.

### Implementation Approach

**Option A: Direct Anthropic Go SDK** (simpler, recommended for personal use)

Add `github.com/anthropics/anthropic-sdk-go` to `go.mod`. Create an AI adapter that calls Claude's Messages API with tool_use for structured output.

```
// This is conceptual — the skill would implement the actual code
1. Define domain ports: Categorizer, InsightGenerator, SearchEngine
2. Implement AI adapter using anthropic-sdk-go
3. Add prompt templates to internal/adapter/ai/prompts/
4. Wire in main.go like any other adapter
5. Add API endpoints for AI features
6. Frontend: conversation UI or inline AI suggestions
```

**Option B: Managed Agent** (more powerful, better for multi-turn interactions)

Deploy a Claude managed agent with tools that can query your database. The Go backend proxies requests to the agent. Better for complex multi-turn conversations ("let me dig deeper into your restaurant spending...").

### Recommendation

Start with **Option A** for transaction categorization — it's a single API call, fits cleanly into the hexagonal architecture, and delivers immediate value. Consider Option B when you want multi-turn AI conversations.

---

## Part 8: Skill Refinements

### 8.1 Skill Deduplication Strategy

Both repos have nearly identical skills (same 8 commands). The differences are domain-specific (Go review checklist vs React review checklist). Options:

| Approach | Pros | Cons |
|---|---|---|
| Keep separate (current) | Each repo is self-contained | Maintenance burden, drift risk |
| Shared base + project overrides | DRY, single source of truth for workflow | Requires workspace setup |
| Template-based generation | Generate skills from a template per project | Over-engineering for 2 repos |

**Recommendation:** Keep separate for now. The skills are mature and the differences are intentional (domain-specific checklists). If you add a third project, then extract shared workflow to the workspace level.

### 8.2 New Skills to Add

#### `/project:triage` (Both Projects)

When a bug is reported or an error occurs in production:
```
1. Read the error/bug description
2. Search codebase for related code paths
3. Identify potential root causes
4. Suggest which existing tests should have caught it
5. Propose a fix approach and which files to modify
6. Create a GitHub issue if one doesn't exist
```

#### `/project:debt` (Both Projects)

Technical debt tracker:
```
1. Scan for TODO/FIXME/HACK comments
2. Check for known code smells (large files, deep nesting, unused exports)
3. Cross-reference with GitHub issues
4. Report: tracked debt (has an issue) vs untracked debt (needs an issue)
5. Optionally create issues for untracked debt
```

#### `/project:e2e-verify` (pfm-ui-react)

After implementing a UI feature, run Playwright E2E tests with visual verification:
```
1. Start the dev server
2. Run relevant Playwright specs
3. If new feature, suggest what E2E test to write
4. Capture screenshots for visual regression tracking
```

#### `/project:openapi-check` (pfm-go)

After modifying any HTTP handler:
```
1. Run swag to regenerate the OpenAPI spec
2. Diff against the committed spec
3. If changed, verify the changes match the handler modifications
4. Flag any breaking changes (removed fields, changed types)
```

### 8.3 Existing Skill Improvements

#### `/project:implement` Enhancement: Auto-Memory

After completing a story, automatically save a memory entry with:
- What was built (one line)
- Any non-obvious decisions made during implementation
- Any patterns established that future stories should follow

This feeds the memory system (Part 9) and gives future sessions context about past work.

#### `/project:ship` Enhancement: Cross-Repo Awareness

When shipping a backend change that affects the API:
```
After Step 6 (squash-merge), check:
- Does this PR change any HTTP handler or OpenAPI spec?
- If yes, create a GitHub issue in pfm-ui-react: "Frontend: update for API change in pfm-go#N"
```

This closes the loop between backend and frontend without requiring the full workspace setup.

#### `/project:review` Enhancement: Performance Baseline

Add a new category to both review checklists:

For pfm-go:
```
## Performance
- [ ] No N+1 queries (JOINs or batch queries instead of loops)
- [ ] Database queries use indexes (check EXPLAIN plan for new queries)
- [ ] No unbounded result sets (LIMIT/OFFSET or cursor pagination)
- [ ] Large operations use streaming (io.Reader/Writer) not buffering
```

For pfm-ui-react:
```
## Bundle Size
- [ ] No new dependency >50KB without justification
- [ ] Dynamic imports for routes/features (code splitting)
- [ ] Images optimized (WebP, appropriate dimensions)
```

---

## Part 9: Memory System Bootstrap

Your memory system is empty. Here's what to seed based on what I've learned in this session.

### Memories to Create

1. **user_profile.md** — Your role, goals, workflow preferences
2. **project_pfm_overview.md** — What PFM is, its current state, the two repos
3. **feedback_workflow.md** — The "I orchestrate, Claude codes" principle and its implications
4. **reference_project_links.md** — Repo URLs, deployment URLs, API docs
5. **project_architecture_decisions.md** — Key decisions that shouldn't be re-debated

These will be created after you approve this plan.

---

## Part 10: Implementation Roadmap

### Phase 1: Foundation (This Week) — Low Effort, High Impact

- [ ] Clean up pfm-go `settings.local.json` (Part 3)
- [ ] Add Branch Guard hook to both projects (Part 2, Hook 1)
- [ ] Add Import Rule Enforcer hook to pfm-go (Part 2, Hook 3)
- [ ] Bootstrap memory system with initial entries (Part 9)
- [ ] Add Test File Existence Guard hook to both projects (Part 2, Hook 4)

**Estimated effort:** 1-2 sessions

### Phase 2: Workflow Enhancement (Next 2 Weeks) — Medium Effort

- [ ] Add `/project:triage` skill to both projects (Part 8.2)
- [ ] Add `/project:debt` skill to both projects (Part 8.2)
- [ ] Add `/project:openapi-check` to pfm-go (Part 8.2)
- [ ] Enhance `/project:ship` with cross-repo awareness (Part 8.3)
- [ ] Add Lint-on-Save hooks to both projects (Part 2, Hook 2)
- [ ] Add Performance category to both review checklists (Part 8.3)

**Estimated effort:** 3-4 sessions

### Phase 3: Cross-Project Orchestration (Month 2) — Medium-High Effort

- [ ] Set up `pfm-workspace/` directory with shared CLAUDE.md (Part 4)
- [ ] Create `/project:api-sync` skill (Part 4)
- [ ] Create `/project:full-stack` skill (Part 4)
- [ ] Create `/project:release` skill (Part 4)
- [ ] Set up OpenAPI → TypeScript type generation pipeline

**Estimated effort:** 4-6 sessions

### Phase 4: Automation (Month 2-3) — Medium Effort

- [ ] Set up Nightly Quality Sentinel (Part 5, Agent 1)
  - Either via CronCreate (if on supported plan) or GitHub Actions with claude-code-action
- [ ] Set up Weekly Dependency Health Check (Part 5, Agent 2)
- [ ] Set up API Contract Drift Detector (Part 5, Agent 3)
- [ ] Set up Coverage Trend Tracker (Part 5, Agent 4)

**Estimated effort:** 3-4 sessions

### Phase 5: Product AI (Month 3+) — High Effort, High Value

- [ ] Add Anthropic Go SDK to pfm-go
- [ ] Define domain ports for AI features (Categorizer, InsightGenerator)
- [ ] Implement Claude AI adapter
- [ ] Add transaction auto-categorization endpoint
- [ ] Build frontend UI for AI interactions
- [ ] Add spending insights feature
- [ ] Evaluate managed agents for multi-turn AI assistant

**Estimated effort:** Full milestone (5-10 stories)

---

## Appendix A: Decision Matrix — Where Each Claude Platform Feature Fits

| Platform Feature | Best For | Your Use Case |
|---|---|---|
| **Skills (commands/)** | Repeatable multi-step workflows | Already excellent. Add triage, debt, api-sync |
| **Hooks (settings.json)** | Automated guardrails and enforcement | Branch protection, architecture enforcement, lint |
| **CLAUDE.md** | Convention documentation | Already excellent. Keep evolving |
| **Memory** | Cross-session context persistence | Bootstrap now, auto-populate from skills |
| **Scheduled Agents (CronCreate)** | Recurring maintenance tasks | Nightly quality, weekly deps, coverage trends |
| **Remote Triggers** | Event-driven automation | API drift detection after deploys |
| **MCP Servers** | Custom tool integration | Potential: PFM-specific tools for Claude |
| **Claude API (in product)** | AI features for end users | Transaction categorization, insights |
| **Managed Agents** | Persistent, stateful AI services | PFM AI assistant (future) |
| **Subagents (code-reviewer, etc.)** | Parallel analysis within a session | Already used implicitly by skills |

## Appendix B: What NOT to Do

1. **Don't over-automate before the product features are built.** Hooks and scheduled agents are appealing but the highest-value work is still implementing households, accounts, and transactions in the frontend. Don't let meta-work crowd out product work.

2. **Don't build a monorepo.** Two separate repos with a lightweight workspace directory is the right call for your scale. Monorepo tooling (Nx, Turborepo) would add complexity without proportional benefit.

3. **Don't add Claude API to the product before the core is done.** Transaction categorization is compelling but requires a working ledger with real transactions flowing through it. Build the plumbing first.

4. **Don't extract shared skill templates yet.** With only two repos, the maintenance burden of separate skills is low. Extract when (if) a third project arrives.

5. **Don't use managed agents for development orchestration.** Your Claude Code skills already handle this well. Managed agents shine for product features (the AI assistant) and operational tasks (monitoring, alerting), not for dev workflow.
