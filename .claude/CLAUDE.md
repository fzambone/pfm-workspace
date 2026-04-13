# Personal Preferences & Workflow Rules

## Workflow Rules

- **I orchestrate, Claude codes.** I make architectural and product decisions. Claude writes all code, creates all files, and produces all implementation. I do not type code.
- **One step at a time.** One file or one logical unit per step. Pause at decisions that affect architecture or approach.
- **Claude runs git and gh commands autonomously.** Commits and pushes require my explicit instruction.
- **Fetch GitHub issues via `gh`.** Use `gh issue view <N>` to read issue details and acceptance criteria.
- **Cross-project work references both repos.** When an issue requires changes in pfm-go or pfm-ui-react, specify exact file paths relative to those repos.

## Decision Points — Always Stop and Ask

Stop and surface a decision when:
- A change affects both repos simultaneously
- A hook or skill could have unintended side effects on the development workflow
- A new dependency or tool is needed in either repo
- The approach for a scheduled agent could impact CI/CD pipelines
