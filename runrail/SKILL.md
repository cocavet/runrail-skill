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

## User-Facing Communication

- Start the task promptly instead of listing internal steps or a detailed plan.
- Keep user-facing updates short and milestone-based.
- Only notify meaningful progress such as: starting, waiting for required input, blocked, or completed.
- Do not narrate intermediate steps, internal checks, route selection, variable resolution, or step-by-step execution.
- If a status message is useful while resolving, keep it to a short `Connecting ...` style update.
- Keep the final response concise and focused on outcome, blockers, or next action.

## Strict Execution

- Treat the resolved API payload as the source of truth.
- Follow the published route, prompts, inputs, step order, and output exposure exactly.
- Do not invent steps, merge steps, skip steps, reorder execution, rewrite runtime inputs, or change the route.
- Treat empty runtime input values as optional null-equivalents. If an input arrives empty, blank, or effectively unset, ignore it instead of treating it as a blocker or asking for it again.
- If required data is missing, inconsistent, or unresolved, stop and state the exact blocker.
- Begin execution as soon as the run is resolved and required inputs are known.
- Do not announce each published step to the user; only surface milestone updates or blockers.

When running in strict execution mode, read [references/execution-contract.md](references/execution-contract.md) before proceeding.

Use the bundled helper when you need to resolve a token:

```bash
python3 scripts/resolve_playbook.py --execution-token "<executionToken>"
```

## Design Mode

- Define the workflow goal first.
- Prefer short steps with one responsibility each.
- Make inputs, variables, and outputs explicit.
- Mark optional inputs clearly and document that empty values should be treated as `null` and ignored.
- Use structured outputs when later steps depend on them.
- Preserve business intent while improving reliability.
- Do the design work directly instead of narrating intermediate reasoning unless the user explicitly asks for it.

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
