# Coordinated Platform Release

Deploy the PFM platform in the correct order: backend first, health check gate, then frontend.
Verifies CI passes in both repos before deploying. Reports failure with rollback guidance.

Use this skill when:
- Deploying a new feature that spans both pfm-go and pfm-ui-react
- Deploying a backend-only change (frontend phase will be skipped gracefully)
- You need coordinated, ordered deployment with health verification between steps

Do NOT use for:
- Database schema migrations — these run automatically at app startup (per pfm-go design)
- Rolling back a failed deployment — this skill suggests rollback steps; execute them manually
- Development environment setup

---

## Phase 1 — Pre-Flight Checks

### 1.1 Verify both repos are on main with clean status

```
cd /Users/fzambone/projects/go/pfm-go
git status
git log -1 --oneline

cd /Users/fzambone/projects/pfm-ui-react
git status
git log -1 --oneline
```

**Requirements:**
- Both repos must be on `main` branch
- Both repos must have no uncommitted changes (`git status` clean)
- Both repos must be up to date with `origin/main`

If any repo is not on main, has uncommitted changes, or is behind origin: **stop and report**:

```
Pre-flight FAILED
  pfm-go:         <on main ✓ / on <branch> ✗> | <clean ✓ / dirty ✗> | <up to date ✓ / behind ✗>
  pfm-ui-react:   <on main ✓ / on <branch> ✗> | <clean ✓ / dirty ✗> | <up to date ✓ / behind ✗>

Resolve the above before releasing. Run /project:ship first if changes are uncommitted.
```

### 1.2 Run CI in both repos

```
cd /Users/fzambone/projects/go/pfm-go
make ci

cd /Users/fzambone/projects/pfm-ui-react
pnpm ci
```

Both must pass. If either fails: **stop and report the failure**. Do not deploy with a failing CI.

```
Pre-flight FAILED — CI gate did not pass
  pfm-go:       make ci <PASS ✓ / FAIL ✗>
  pfm-ui-react: pnpm ci <PASS ✓ / FAIL ✗>

Fix the CI failure before releasing.
```

### 1.3 Report pre-flight result

```
Pre-flight: PASS
  pfm-go:       main ✓ | clean ✓ | CI ✓
  pfm-ui-react: main ✓ | clean ✓ | CI ✓
```

---

## Phase 2 — Backend Deploy

### 2.1 Deploy to Fly.io

```
cd /Users/fzambone/projects/go/pfm-go
fly deploy
```

**What to watch for:**
- Fly.io will build the Docker image and release the new version
- Deployment typically takes 2–5 minutes
- A successful deploy ends with: `Visit your newly deployed app at https://pfm-go-api.zambone.dev`

### 2.2 Handle deploy failure

If `fly deploy` exits non-zero:

```
Backend deploy FAILED
  Error: <error output from fly deploy>

Rollback steps:
  1. Check recent deployments:  fly releases --app pfm-go-api
  2. Roll back to previous:     fly deploy --image <previous-image-ref>
     (find <previous-image-ref> in the releases list above)
  3. Verify rollback health:    curl -sf https://pfm-go-api.zambone.dev/health/ready

Frontend deploy: SKIPPED (backend did not succeed)
```

**Stop here.** Do not proceed to the health gate or frontend deploy.

---

## Phase 3 — Backend Health Gate

After `fly deploy` succeeds, wait for the backend to become healthy before deploying
the frontend. This ensures the frontend never calls endpoints that aren't yet live.

### 3.1 Poll the health endpoint

```
curl -sf https://pfm-go-api.zambone.dev/health/ready
```

Retry up to **12 times** with **15-second intervals** (3 minutes total).

- HTTP 200 → health check PASS — proceed to Phase 4
- Non-200 or connection refused → wait 15 seconds and retry
- After 12 retries without success → report timeout

### 3.2 Handle health check timeout

```
Backend health gate TIMED OUT after 3 minutes
  URL: https://pfm-go-api.zambone.dev/health/ready
  Last response: <status code or "connection refused">

Investigation steps:
  1. Check Fly.io status:     fly status --app pfm-go-api
  2. Check recent logs:       fly logs --app pfm-go-api
  3. Check machine state:     fly machine list --app pfm-go-api

If the app is crash-looping, consider rollback:
  1. List releases:   fly releases --app pfm-go-api
  2. Roll back:       fly deploy --image <previous-image-ref>

Frontend deploy: SKIPPED (backend health check did not pass)
```

**Stop here.** Do not deploy the frontend if the backend is unhealthy.

### 3.3 Report health gate result

```
Backend health gate: PASS
  https://pfm-go-api.zambone.dev/health/ready → 200 OK
```

---

## Phase 4 — Frontend Deploy

### 4.1 Check if frontend deployment is configured

Look for a deploy script or configuration in pfm-ui-react:

```
cd /Users/fzambone/projects/pfm-ui-react
cat package.json | grep -i deploy
```

Also check for deployment config files:
- `fly.toml` — Fly.io
- `vercel.json` — Vercel
- `.github/workflows/deploy*.yml` — CI-triggered deploy

**If no deploy mechanism is found:**

```
Frontend deploy: NOT CONFIGURED
  No deploy script found in package.json and no deployment config detected.
  The frontend deployment pipeline has not been set up yet.

To configure frontend deployment:
  - For Fly.io:  add fly.toml and run `fly launch` in pfm-ui-react
  - For Vercel:  run `vercel` CLI from pfm-ui-react
  - For other:   add a "deploy" script to package.json

Skipping frontend deploy. Backend is live at https://pfm-go-api.zambone.dev
```

Continue to Phase 5 (summary) with frontend marked as NOT CONFIGURED.

### 4.2 Deploy frontend (when configured)

Run the configured deploy command. Examples:

- Fly.io: `fly deploy --app <pfm-ui-app-name>`
- Vercel: `pnpm run deploy` (if configured in package.json)
- Other: whatever deploy script is present

### 4.3 Handle frontend deploy failure

If the frontend deploy fails:

```
Frontend deploy FAILED
  Error: <error output>

The backend is already live. To restore consistency:
  Option A — Fix the frontend issue and re-run /project:release
  Option B — If the frontend change is incompatible with the live backend:
    1. Roll back backend:  fly deploy --image <previous-image-ref> --app pfm-go-api
    2. Verify backend:     curl -sf https://pfm-go-api.zambone.dev/health/ready

Backend remains live at: https://pfm-go-api.zambone.dev
```

---

## Phase 5 — Summary

Report the full deployment outcome:

```
Release Summary — <date>
────────────────────────────────────────────────

Pre-flight:     PASS
  pfm-go CI:       make ci ✓
  pfm-ui-react CI: pnpm ci ✓

Backend deploy: SUCCESS
  App:    pfm-go-api (Fly.io, region: gru)
  URL:    https://pfm-go-api.zambone.dev
  Health: https://pfm-go-api.zambone.dev/health/ready → 200 OK ✓

Frontend deploy: <SUCCESS | NOT CONFIGURED | FAILED>
  <URL if deployed | "Pipeline not configured — see Phase 4 for setup instructions">

────────────────────────────────────────────────
Verification links:
  API health:   https://pfm-go-api.zambone.dev/health/ready
  API docs:     https://pfm-go-api.zambone.dev/docs
  <Frontend URL if deployed>

Next steps:
  <If all success>:         Smoke test the deployed features end-to-end
  <If frontend skipped>:    Set up frontend deployment pipeline (see Phase 4)
  <If any failure>:         Follow rollback steps above before next attempt
```
