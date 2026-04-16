---
name: runrail
description: Help with RunRail playbooks, prompts, runs, variables, and workflow design. Use when Codex needs to create, edit, review, debug, or execute RunRail workflows.
---

# RunRail

Use this skill for RunRail playbooks and agent executions.

## Mode Selection

- If the user provides an `executionToken` or a payload with `kind: "runrail-agent-execution"`, enter strict execution mode.
- Otherwise, use design mode for creating, editing, reviewing, or improving a playbook.
- Do not mix execution and design unless the user explicitly asks for both.

## Strict Execution

- Treat the resolved API payload as the source of truth.
- Follow the published route, prompts, inputs, step order, and output exposure exactly.
- Do not invent steps, merge steps, skip steps, reorder execution, rewrite runtime inputs, or change the route.
- If required data is missing, inconsistent, or unresolved, stop and state the exact blocker.
- Keep narration minimal; before input questions, only show a short `Connecting ...` status while resolving.

When running in strict execution mode, read [references/execution-contract.md](references/execution-contract.md) before proceeding.

Use the bundled helper when you need to resolve a token:

```bash
python3 scripts/resolve_playbook.py --execution-token "<executionToken>"
```

## Design Mode

- Define the workflow goal first.
- Prefer short steps with one responsibility each.
- Make inputs, variables, and outputs explicit.
- Use structured outputs when later steps depend on them.
- Preserve business intent while improving reliability.

## Prompt Writing

- State task, context, and constraints.
- Name the variables the step receives.
- Specify the expected output format.
- Prefer precise instructions over stylistic wording.

## Review Focus

- unclear goals
- missing or inconsistent variables
- outputs that downstream steps cannot consume reliably
- steps doing too many things at once
- missing failure handling
