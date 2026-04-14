# Full-Stack Feature Implementation

Implement a feature that spans both pfm-go (backend) and pfm-ui-react (frontend) in a single
session. Runs the backend phase first, gates on `/project:api-sync` to verify the contract,
then runs the frontend phase. CI gates run in both repos before shipping.

Use this skill when:
- A new API endpoint needs a corresponding frontend UI
- A frontend feature requires a new or modified backend endpoint
- You want guaranteed contract consistency between a backend and frontend change

Do NOT use for:
- Backend-only changes (use pfm-go `/project:implement` directly)
- Frontend-only changes (use pfm-ui-react `/project:implement` directly)
- Deployment (use `/project:release`)

---

## Phase 1 — Setup

### 1.1 Identify the feature

- If invoked with a GitHub issue number (e.g. `/project:full-stack 42`): load it with
  `gh issue view 42` and extract the goal, acceptance criteria, and scope.
- If invoked with a free-text description: use that description as the feature goal.
- If neither: ask "What feature should I implement? (issue number or description)"

### 1.2 Verify dependencies

```
gh issue view <N> --json body
```

Check the **Depends On** section. All listed issues must be CLOSED before proceeding.

### 1.3 Create branches

Create a feature branch in each target repo:

```
cd /Users/fzambone/projects/go/pfm-go
git checkout main && git pull
git checkout -b feat/<scope>-<description>-<N>

cd /Users/fzambone/projects/pfm-ui-react
git checkout main && git pull
git checkout -b feat/<scope>-<description>-<N>
```

Use the same branch name in both repos so cross-references are clear.
`<N>` is the issue number if available; omit if feature-description only.

### 1.4 Write a dual-repo plan

Before any implementation, write a plan covering both repos. Stop and present it.
The plan must include:

```
## Feature goal
One sentence.

## Backend (pfm-go)
- Files to create or modify
- New endpoints: METHOD /api/v1/<path>
- Domain changes (types, ports, adapters)
- Test strategy

## Contract
- Request schema: { field: type, ... }
- Response schema: { field: type, ... }
- HTTP method and path

## Frontend (pfm-ui-react)
- Files to create or modify (feature, components, hooks, types, api)
- TypeScript types needed
- UI behaviour

## Open decisions
- List any ambiguities
```

**Stop here and wait for confirmation before Phase 2.**

---

## Phase 2 — Backend Phase (pfm-go)

Follow pfm-go conventions exactly. Per pfm-go CLAUDE.md:

### 2.1 Architecture layers (in order)

Implement bottom-up through the hexagonal layers:

1. **Domain** (`internal/domain/`) — types, business rules, no I/O
2. **Port** (`internal/port/`) — interfaces the domain needs
3. **Adapter: Postgres** (`internal/adapter/postgres/`) — sqlc queries + goose migrations
4. **Adapter: HTTP** (`internal/adapter/http/`) — handler, route wiring
5. **Wiring** (`cmd/api/main.go` or equivalent) — wire new dependencies

### 2.2 TDD Red→Green cycle

For each layer:
1. Write the test first (`_test.go` file). Run — confirm it FAILS.
2. Write the implementation. Run — confirm it PASSES.
3. Refactor if needed. Run — confirm it still PASSES.

Run unit tests: `make test`
Run integration tests: `make test-integration`

### 2.3 Go conventions to enforce

- Error sentinels in `internal/message/` — never define inline
- Validation via `validate.NewResult()` in `internal/platform/validate/`
- Money as `int64` (minor units) — never float
- Response helpers: `WriteJSON`, `WriteCreated`, `WriteNoContent`, `WriteError`, `WriteValidationError`
- HTTP status codes per workspace CLAUDE.md error mapping
- OpenAPI annotations on every new handler (`// @Summary`, `// @Router`, etc.)
- Run `make check-openapi` after adding handlers — fix drift before proceeding

### 2.4 Backend complete gate

Before proceeding to Phase 3, verify:
```
cd /Users/fzambone/projects/go/pfm-go
make ci
```

All steps must pass. Do not proceed to the contract gate if `make ci` fails.

---

## Phase 3 — Contract Gate

After `make ci` passes in pfm-go, run the API contract check.

### 3.1 Regenerate the spec

```
cd /Users/fzambone/projects/go/pfm-go
make generate
```

This updates `api/swagger.yaml` to reflect the new endpoint.

### 3.2 Run api-sync

```
/project:api-sync
```

Expected result: the new endpoint appears as **MISSING** (no frontend types yet).
Any **DRIFT** on existing endpoints must be resolved before proceeding.

### 3.3 Gate decision

| api-sync result | Action |
|---|---|
| New endpoint MISSING only | Proceed to Phase 4 — frontend will add the types |
| Existing endpoint DRIFT | **Stop.** Fix the TypeScript types in pfm-ui-react to match, then re-run api-sync |
| Spec fetch fails | **Stop.** Run `make generate` again and retry |

Report:
```
Contract gate: PASS
New endpoint: <METHOD> <path> — MISSING (will be added in frontend phase)
Existing endpoints: all MATCH
```

---

## Phase 4 — Frontend Phase (pfm-ui-react)

Follow pfm-ui-react conventions exactly. Per pfm-ui-react CLAUDE.md:

### 4.1 Feature structure

All new code goes into `src/features/<resource>/`:

```
src/features/<resource>/
  api/          # API call functions (fetch wrappers)
  components/   # React components for this feature
  hooks/        # Custom hooks
  types.ts      # TypeScript interfaces for this feature
  index.ts      # Public exports
```

### 4.2 TypeScript types first

Before writing components or API calls, add the TypeScript interfaces for the new endpoint.
Use `/project:api-sync` type generation (Phase 5 — "y" to generate) as a starting point,
then adjust to match the frontend's camelCase conventions.

Fields must match the spec with the following mapping:
- `snake_case` JSON keys → `camelCase` TypeScript fields
- `integer` → `number`
- `string` → `string`
- `boolean` → `boolean`

### 4.3 API call function

Write a typed fetch wrapper in `src/features/<resource>/api/<endpoint>.ts`:
- Returns the TypeScript interface on success
- Throws a typed error class on failure
- Sends `Authorization: Bearer <token>` header for protected routes
- Uses `API_BASE_URL` prefix (from env or empty string)

### 4.4 TDD Red→Green cycle

For each component and hook:
1. Write the test first. Run `pnpm test` — confirm it FAILS.
2. Write the implementation. Run `pnpm test` — confirm it PASSES.
3. Refactor if needed. Confirm still PASSES.

### 4.5 Accessibility requirements

- Interactive elements must have accessible names (aria-label or visible label)
- Form inputs must be associated with labels (`htmlFor` / `id` pair)
- Error messages must be announced (role="alert" or aria-live)
- Keyboard navigation must work (no mouse-only interactions)
- Use Testing Library `getByRole` queries in tests (not by test-id or class)

### 4.6 Styling

- Tailwind utility classes only — no inline styles
- Class merging via `cn()` from `src/shared/utils/cn.ts`
- No new design tokens without approval

### 4.7 Frontend complete gate

Before Phase 5, verify:
```
cd /Users/fzambone/projects/pfm-ui-react
pnpm ci
```

All steps must pass (lint + type-check + test + build).

---

## Phase 5 — CI Gates + Verification

### 5.1 Run both CI gates

```
cd /Users/fzambone/projects/go/pfm-go && make ci
cd /Users/fzambone/projects/pfm-ui-react && pnpm ci
```

Both must pass before proceeding.

### 5.2 Run api-sync final check

```
/project:api-sync
```

Expected: the new endpoint now shows **MATCH**. No DRIFT or MISSING on any endpoint.

### 5.3 Run verify-issue

```
/project:verify-issue
```

All acceptance criteria must be COVERED.

### 5.4 Run review

```
/project:review
```

All categories must PASS.

---

## Phase 6 — Ship

### 6.1 Commit and push — pfm-go

```
cd /Users/fzambone/projects/go/pfm-go
git add <files>
git commit -m "$(cat <<'EOF'
feat(<scope>): <imperative description>

- Backend bullet 1
- Backend bullet 2

refs fzambone/pfm-workspace#<N>
EOF
)"
git push -u origin <branch-name>
```

### 6.2 Commit and push — pfm-ui-react

```
cd /Users/fzambone/projects/pfm-ui-react
git add <files>
git commit -m "$(cat <<'EOF'
feat(<scope>): <imperative description>

- Frontend bullet 1
- Frontend bullet 2

refs fzambone/pfm-workspace#<N>
EOF
)"
git push -u origin <branch-name>
```

### 6.3 Create PRs with cross-references

Create the pfm-go PR first:

```
gh pr create --repo fzambone/pfm-go \
  --title "feat(<scope>): <description>" \
  --body "$(cat <<'EOF'
## Summary
- Backend bullet 1
- Backend bullet 2

## Workspace Issue
Implements fzambone/pfm-workspace#<N>

## Frontend PR
fzambone/pfm-ui-react#<TBD — fill in after creating>

## Verification
- [x] make ci: PASS
- [x] /project:api-sync: MATCH
- [x] /project:review: PASS
EOF
)"
```

Then create the pfm-ui-react PR, referencing the pfm-go PR number:

```
gh pr create --repo fzambone/pfm-ui-react \
  --title "feat(<scope>): <description>" \
  --body "$(cat <<'EOF'
## Summary
- Frontend bullet 1
- Frontend bullet 2

## Workspace Issue
Implements fzambone/pfm-workspace#<N>

## Backend PR
fzambone/pfm-go#<pfm-go-PR-number>

## Verification
- [x] pnpm ci: PASS
- [x] /project:api-sync: MATCH
- [x] /project:review: PASS
EOF
)"
```

Update the pfm-go PR body to include the pfm-ui-react PR number.

### 6.4 Merge in order

Merge backend first, then frontend:

```
gh pr merge <pfm-go-PR-number> --repo fzambone/pfm-go --squash --delete-branch
gh pr merge <pfm-ui-react-PR-number> --repo fzambone/pfm-ui-react --squash --delete-branch
```

### 6.5 API impact check

After merging pfm-go:

```
gh -R fzambone/pfm-go pr diff <pfm-go-PR-number> --name-only
```

If `internal/adapter/http/` or `api/swagger.yaml` appear: the frontend PR covers the
contract change — note this in the report rather than creating a separate tracking issue.

### 6.6 Sync main in both repos

```
cd /Users/fzambone/projects/go/pfm-go && git checkout main && git pull
cd /Users/fzambone/projects/pfm-ui-react && git checkout main && git pull
```

### 6.7 Close workspace issue

If not auto-closed:
```
gh issue close <N> --comment "Implemented across pfm-go and pfm-ui-react. See linked PRs."
```

### 6.8 Report

```
Workspace Issue:  #<N> — <title>
Repos changed:    pfm-go, pfm-ui-react

Per-repo PRs:
  pfm-go:         #<number> — <url> (merged ✓)
  pfm-ui-react:   #<number> — <url> (merged ✓)
  pfm-workspace:  N/A

CI gates:
  pfm-go:         make ci PASS ✓
  pfm-ui-react:   pnpm ci PASS ✓

Contract:         /project:api-sync MATCH ✓
Workspace issue:  closed ✓
All repos:        main synced ✓

Issue #<N> is done.
```
