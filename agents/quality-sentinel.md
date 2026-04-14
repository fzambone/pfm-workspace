# Nightly Quality Sentinel

Autonomous scheduled agent that checks the health of main in pfm-go and pfm-ui-react
nightly and opens GitHub issues for any failures or vulnerability advisories.

## Trigger Configuration

| Field | Value |
|---|---|
| **Trigger ID** | `trig_015qgaAJV8ets33NiAwTC1SU` |
| **Schedule** | `7 5 * * *` UTC = **2:07 AM America/Sao_Paulo** (nightly) |
| **Model** | claude-sonnet-4-6 |
| **Environment** | Full Internet test (`env_01JQKbBzh5FGLT1htjVV2eX6`) |
| **Sources** | `github.com/fzambone/pfm-go`, `github.com/fzambone/pfm-ui-react` |
| **Manage** | https://claude.ai/code/scheduled/trig_015qgaAJV8ets33NiAwTC1SU |

## What It Does

1. Checks the latest GitHub Actions CI run on `main` in each repo
2. Checks for open HIGH/CRITICAL Dependabot vulnerability alerts
3. If all checks pass and no alerts: **exits silently** (no issue created)
4. If any check fails: opens a GitHub issue in the affected repo with:
   - CI run link and failure details (first 80 lines of failed logs)
   - Open vulnerability alerts with severity and package
   - Suggested fix steps

## Implementation Notes

The agent runs in Anthropic's CCR cloud environment — it does NOT have access to the
local machine. Rather than running `make ci` / `pnpm ci` directly (which would require
Go toolchain, Docker, golangci-lint, pnpm, etc.), the agent uses the `gh` CLI to:
- Query GitHub Actions workflow run results (`gh run list`, `gh run view --log-failed`)
- Query Dependabot security alerts (`gh api /repos/.../dependabot/alerts`)

This is functionally equivalent to running CI locally: GitHub Actions runs `make ci`
on every push to main, so checking its result catches the same failures.

## Failure Labels

Issues opened by the sentinel use the `sentinel` label in each target repo.
To suppress a false positive, close the issue with a comment explaining why.

## Operational Runbook

### View trigger status
```
https://claude.ai/code/scheduled/trig_015qgaAJV8ets33NiAwTC1SU
```

### Run manually (test a run now)
Use the RemoteTrigger tool in a Claude Code session:
```
RemoteTrigger({ action: "run", trigger_id: "trig_015qgaAJV8ets33NiAwTC1SU" })
```

### Update the schedule or prompt
Use the RemoteTrigger tool:
```
RemoteTrigger({
  action: "update",
  trigger_id: "trig_015qgaAJV8ets33NiAwTC1SU",
  body: { "cron_expression": "<new-cron>" }
})
```

### Disable the sentinel
```
RemoteTrigger({
  action: "update",
  trigger_id: "trig_015qgaAJV8ets33NiAwTC1SU",
  body: { "enabled": false }
})
```

### Delete the sentinel
Cannot be done via API. Go to: https://claude.ai/code/scheduled

## Related Issues

- Workspace issue: fzambone/pfm-workspace#22
- Parent epic: fzambone/pfm-workspace#21 (M4: Autonomous Maintenance)
