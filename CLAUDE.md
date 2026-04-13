# PFM Workspace — Cross-Project Orchestration

## Identity

This is the **workspace repo** for the PFM (Personal Finance Manager) platform. It coordinates work across two implementation repos:

- **pfm-go** — Go backend at `../go/pfm-go/` (github.com/fzambone/pfm-go)
- **pfm-ui-react** — React frontend at `../pfm-ui-react/` (github.com/fzambone/pfm-ui-react)

## Purpose

1. **Project management** — Milestones and issues for cross-cutting work (AI harness engineering, infrastructure, coordination)
2. **Shared skills** — Claude Code skills that orchestrate work across both repos
3. **Cross-project context** — CLAUDE.md rules that apply when working across repos

## Repo References

| Concern | Location | URL |
|---|---|---|
| Backend code | `../go/pfm-go/` | github.com/fzambone/pfm-go |
| Frontend code | `../pfm-ui-react/` | github.com/fzambone/pfm-ui-react |
| Backend API | — | https://pfm-go-api.zambone.dev |
| OpenAPI spec | — | https://pfm-go-api.zambone.dev/api/v1/openapi.yaml |
| API docs | — | https://pfm-go-api.zambone.dev/docs |

## Cross-Project Rules

1. **Backend deploys before frontend.** Always verify backend health before deploying frontend changes that depend on new endpoints.
2. **OpenAPI is the contract.** When implementing frontend API calls, fetch the OpenAPI spec first. Never guess endpoint shapes.
3. **Money is int64.** Both repos use minor units (cents/centavos) as integers. No floats anywhere in the stack.
4. **Conventional Commits** in all repos. Same format: `type(scope): description` + `closes #N`.
5. **Each repo's CLAUDE.md is authoritative** for that repo's conventions. This workspace CLAUDE.md adds cross-project coordination rules only.

## Milestones

This repo tracks the AI Harness Engineering Plan:

- **M1** — Foundation: Hooks, Settings & Memory
- **M2** — Workflow Enhancement: New Skills & Review Upgrades
- **M3** — Cross-Project Orchestration
- **M4** — Autonomous Maintenance: Scheduled Agents
- **M5** — Product AI: Claude API Integration
