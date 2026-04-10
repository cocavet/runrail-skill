---
name: runrail
description: Help with RunRail playbooks, prompts, runs, variables, and workflow design. Use when Codex needs to create, edit, review, debug, or execute RunRail workflows, with special emphasis on following the exact API-defined steps and execution path without improvising, skipping, or reordering.
---

# RunRail

Use this skill when working on RunRail playbooks or when turning an operating process into a reusable multi-step workflow.

Treat a RunRail playbook as an ordered sequence of steps. Each step should have a clear job, explicit inputs, and a predictable output that the next step can consume.

When the playbook comes from the RunRail API, treat the resolved payload as the source of truth. Follow the published route exactly. Do not invent helper steps, merge steps, reorder execution, skip prompts, or "improve" the workflow while it is running.

When the user pastes the Runrail agent payload copied from the product, treat it as an execution request, not just a design request.

Preferred payload format:

```json
{
  "kind": "runrail-agent-execution",
  "version": "1",
  "executionToken": "<executionToken>"
}
```

Legacy fallback format:

```text
executionToken: <executionToken>
```

## Core Rule

Execution mode is strict.

- The API-defined playbook is authoritative.
- The published input list is authoritative.
- The published `stepRecords` sequence is authoritative.
- The published step prompt is authoritative.
- The published output exposure rules are authoritative.
- If something required by the API payload is missing, inconsistent, or not executable, stop and say exactly what is wrong.
- Do not switch into redesign, optimization, or advisory mode unless the user explicitly asks for it.

## Mode Selection

- If the user provides `executionToken`, enter execution mode and prioritize the API payload over general workflow advice.
- If the user provides a JSON payload with `kind: "runrail-agent-execution"`, parse `executionToken` from that JSON field exactly. Do not retype, shorten, normalize, or infer the token from surrounding prose.
- If the user asks to create, edit, review, or improve a playbook, enter design mode.
- Do not mix execution mode and design mode in the same response unless the user explicitly asks for both.

## Design Workflow

Use this section only when creating or editing a playbook, not when executing a resolved playbook from the API.

1. Define the end goal before changing prompts or step order.
2. Identify the required inputs, variables, and external context.
3. Break the work into small steps with one responsibility each.
4. Specify the expected output format for every step.
5. Check that downstream steps can consume upstream outputs without ambiguity.
6. Simplify or merge steps only when reliability stays intact.

## Execution Protocol

When the user gives you `executionToken`, execute the playbook in this exact order and do not deviate from the route:

1. Show a short resolve status such as `Connecting [#####..........]` while the resolve call is in flight.
2. Resolve the playbook first with a single API call using the execution token.
3. If the resolve call returns no playbook data, say so plainly and stop instead of pretending the playbook exists.
4. Read the playbook `description`, `globalInstructions`, `inputs`, `steps`, `stepRecords`, and `executionProtocol`.
5. Treat `executionProtocol` as the authoritative runtime contract and follow it literally.
6. Ask for inputs one by one, waiting for the user after each required input.
7. Prefix each input question with its position, such as `1/3`, `2/3`, `3/3`, based on the total number of required inputs.
8. Create the run with a dedicated API call after all required inputs have been collected and before executing the first step.
9. Save the returned `runId` and reuse that exact `runId` for all later reporting calls.
10. Do not start the first step until the run has been created and all required inputs have been collected.
11. Before each step starts, report that step as `running`.
12. Execute exactly one published step at a time.
13. After each step finishes, report that exact step result before moving to the next step.
14. Send exactly one step update per report request.
15. Every step report must include `step.id`, `step.index`, or `step.title`. Prefer `step.id`.
16. Do not send run-level `status: "running"` in `/report`. Use `step.status` instead.
17. Use only the status transitions allowed by `executionProtocol` and the API. In the current strict mode that means `pending -> running -> completed|failed`.
18. Do not report `waiting` or `needs_review` in strict agent execution mode unless the API explicitly allows those transitions.
19. If a step fails, report the failure on that same run and stop.
20. Only after the last published step is complete, report the run as `completed` or `failed` in a separate final run-status request.
21. After the final run-status request, call `GET /runrail/agent/runs/<runId>` and verify the persisted state before claiming success.
22. If the verification response does not match the reports you believe you sent, do not claim completion. Continue reconciling or state the mismatch clearly.
23. Do not add commentary that changes the route of execution unless the user explicitly asks for analysis.
24. Do not call the internal one-shot execution endpoint while in strict agent execution mode.

## API Route Contract

In strict agent execution mode, use these endpoints and no alternative execution path:

1. Resolve the playbook:
   `POST /runrail/agent/resolve`
2. Create the run and get its id:
   `POST /runrail/agent/start`
3. Report progress for that exact run:
   `POST /runrail/agent/runs/<runId>/report`
4. Read the run state if reconciliation is needed:
   `GET /runrail/agent/runs/<runId>`

Do not use `POST /runrail/playbooks/<playbookId>/run` in strict agent execution mode, because that endpoint is the internal one-shot execution path.

Use these minimum valid report payloads:

```json
{"step":{"id":"<stepId>","status":"running"}}
```

```json
{"step":{"id":"<stepId>","status":"completed","output":"<step output>"}}
```

```json
{"step":{"id":"<stepId>","status":"failed","error":{"message":"<error message>"}}}
```

```json
{"status":"completed"}
```

## Resolved Payload Contract

When the resolve API returns a payload like this, interpret it literally:

- `inputs` is the authoritative input list. Each entry may arrive as a compact tuple like `[name, type, example]`.
- `stepRecords` contains the executable step definitions.
- `executionProtocol` is the authoritative route contract for runtime execution and reporting.
- Each `stepRecords` item carries the fields that matter for execution, including `idPost`, `name`, `prompt`, `outputKey`, and `exposeAsOutput`.
- `steps` may appear as a lightweight list of step ids. Use it only to confirm the same route published in `stepRecords`, not to invent a second execution model.
- If `steps` references an id that is missing from `stepRecords`, stop and report that exact missing step id.
- If `stepRecords` is empty, say plainly that there are no executable steps.

Use the helper script in this skill:

```bash
python3 scripts/resolve_playbook.py \
  --execution-token "<executionToken>"
```

Use only this request:

```bash
curl -X POST https://app.runrail.io/api/runrail/agent/resolve \
  -H "Authorization: Bearer <executionToken>" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Input Handling

- Read `description` and `globalInstructions` before asking the first question.
- Keep pre-input narration minimal. The only status text before the first question should be the short `Connecting ...` message while resolving.
- If there are no inputs, state that clearly and continue.
- If inputs arrive as tuples, interpret them as `name`, `type`, `example`.
- Ask for one input at a time.
- When there are multiple required inputs, label each question as `current/total`.
- Use the input type and example when they exist.
- Do not batch all input questions into one message unless the user explicitly asks for that.
- If a required input is missing, do not start the steps.
- Do not ask for extra inputs that are not defined by the resolved playbook unless the user explicitly overrides the playbook.
- If an input is optional in the API payload, do not treat it as required.

## Step Execution

- Run `stepRecords` strictly one by one.
- Treat each `stepRecords` entry as one executable step.
- Before executing each step, announce its position and title, for example `1. Research companies`, `2. Score accounts`, `3. Draft outreach`.
- Use the step `name` as published in the playbook. If a step has no usable name, fall back to `idPost`.
- If a step prompt is empty, stop and explain that the playbook is not executable as published.
- Preserve the raw output of each step.
- If a step has `outputKey`, store the output under that key.
- If a step does not have `outputKey`, store it under a stable fallback key such as `idPost`.
- If `exposeAsOutput` is true, surface that output clearly to the user.
- Do not rewrite a step's intent during execution.
- Do not merge two steps into one response.
- Do not silently recover by guessing what a broken step "probably meant".
- If the API defines a step but the data needed to run it is missing, stop at that step and report the exact blocker.
- Do not skip a `stepRecords` entry, even if it looks trivial.
- Do not send more than one step update in a single report request.
- Do not omit the step identifier in a report. Prefer `step.id` over `step.title`.
- Do not report a later step before the API confirms the earlier step transition.
- Do not claim that a report succeeded unless the API response succeeded.
- After the final report, verify the stored run state before claiming completion.

Resolve placeholders before running each step:

- `{{input.foo}}` and `{{inputs.foo}}` come from user-provided inputs.
- `{{output.foo}}` and `{{outputs.foo}}` come from previous step outputs.
- Ignore harmless whitespace inside the braces.
- If a referenced variable is missing, stop and say exactly which variable could not be resolved.
- Preserve input names exactly as published, including spaces such as `{{inputs.File name}}`.

## Output Discipline

- Do not invent hidden inputs, rules, or steps that are not in the playbook.
- Do not introduce side quests, alternative flows, or extra validations that the API did not define.
- Keep step outputs stable and reusable by later steps.
- If the playbook has no usable steps, say so plainly instead of pretending it ran.
- If the resolve call returns an empty result, print a clear "not found" message instead of leaving the user with a blank response.
- If the playbook and the user request conflict, ask whether to follow the playbook or switch to edit mode before changing the route.

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
- Execute a resolved RunRail playbook exactly as published by the API.
