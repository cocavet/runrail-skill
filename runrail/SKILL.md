---
name: runrail
description: Help with RunRail playbooks, prompts, runs, variables, and workflow design. Use when Codex needs to create, edit, review, debug, or improve RunRail workflows, especially when breaking a process into steps, tightening prompt instructions, or making outputs reliable between steps.
---

# RunRail

Use this skill when working on RunRail playbooks or when turning an operating process into a reusable multi-step workflow.

Treat a RunRail playbook as an ordered sequence of steps. Each step should have a clear job, explicit inputs, and a predictable output that the next step can consume.

When the user pastes the Runrail agent payload copied from the product, treat it as an execution request, not just a design request.

```text
Execute this Runrail playbook with the Runrail skill:
projectId: <projectId>
playbookId: <playbookId>
apiKey: <apiKey>
```

## Workflow

1. Define the end goal before changing prompts or step order.
2. Identify the required inputs, variables, and external context.
3. Break the work into small steps with one responsibility each.
4. Specify the expected output format for every step.
5. Check that downstream steps can consume upstream outputs without ambiguity.
6. Simplify or merge steps only when reliability stays intact.

## Execution Protocol

When the user gives you `projectId`, `playbookId`, and `apiKey`, execute the playbook in this order:

1. Show a short resolve status such as `Connecting [#####..........]` while the resolve call is in flight.
2. Resolve the playbook first with a single API call.
3. If the resolve call returns no playbook data, say so plainly and stop instead of pretending the playbook exists.
4. Read the playbook `description`, `globalInstructions`, and `inputs`.
5. Ask for inputs one by one, waiting for the user after each required input.
6. Prefix each input question with its position, such as `1/3`, `2/3`, `3/3`, based on the total number of required inputs.
7. Run steps in order, resolving placeholders from the collected inputs and previous step outputs.
8. Store each step output so later steps can reference it.

Use the helper script in this skill:

```bash
python3 scripts/resolve_playbook.py \
  --project-id "<projectId>" \
  --playbook-id "<playbookId>" \
  --api-key "<apiKey>"
```

Use only this request:

```bash
curl -X POST https://app.runrail.io/api/runrail/playbooks/resolve \
  -H "Authorization: Bearer <apiKey>" \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": "<projectId>",
    "playbookId": "<playbookId>"
  }'
```

## Input Handling

- Read `description` and `globalInstructions` before asking the first question.
- Keep pre-input narration minimal. The only status text before the first question should be the short `Connecting ...` message while resolving.
- If there are no inputs, state that clearly and continue.
- Ask for one input at a time.
- When there are multiple required inputs, label each question as `current/total`.
- Use the input type and example when they exist.
- Do not batch all input questions into one message unless the user explicitly asks for that.
- If a required input is missing, do not start the steps.

## Step Execution

- Run steps strictly in order.
- Before executing each step, announce its position and title, for example `1. Research companies`, `2. Score accounts`, `3. Draft outreach`.
- Use the step title as published in the playbook. If a step has no usable title, fall back to a stable identifier such as the step id.
- If a step prompt is empty, stop and explain that the playbook is not executable as published.
- Preserve the raw output of each step.
- If a step has `outputKey`, store the output under that key.
- If a step does not have `outputKey`, store it under a stable fallback key such as the step id.
- If `exposeAsOutput` is true, surface that output clearly to the user.

Resolve placeholders before running each step:

- `{{input.foo}}` and `{{inputs.foo}}` come from user-provided inputs.
- `{{output.foo}}` and `{{outputs.foo}}` come from previous step outputs.
- Ignore harmless whitespace inside the braces.
- If a referenced variable is missing, stop and say exactly which variable could not be resolved.

## Output Discipline

- Do not invent hidden inputs, rules, or steps that are not in the playbook.
- Keep step outputs stable and reusable by later steps.
- If the playbook has no usable steps, say so plainly instead of pretending it ran.
- If the resolve call returns an empty result, print a clear "not found" message instead of leaving the user with a blank response.

## Playbook Design

- Prefer short, composable steps over one large prompt.
- Give every step a single responsibility.
- Keep variable names stable and descriptive.
- Make outputs structured when another step will consume them.
- Define fallback behavior for missing data, invalid inputs, or empty results.
- Preserve the business intent of the workflow; do not optimize prompts in a way that changes the outcome.

## Prompt Writing

- Start with the task, context, and constraints.
- List the variables or source data the step receives.
- State exactly what output is expected.
- Prefer explicit instructions over style-heavy wording.
- Avoid vague requests such as "improve this" or "make it better" without success criteria.
- When useful, require JSON, markdown sections, tables, or another stable schema.

## Review Checklist

- Is the goal of the playbook clear?
- Does each step have a defined input and output?
- Are variables named consistently?
- Can another step consume the output without guessing?
- Are failure cases or missing inputs handled?
- Is any step doing too many unrelated things?

## Typical Requests

- Create a new RunRail playbook from a business process.
- Refactor one long prompt into several reliable steps.
- Review a playbook for brittleness, ambiguity, or missing variables.
- Rewrite a step so its output is easier for later steps to consume.
- Tighten a workflow that is producing inconsistent results.
