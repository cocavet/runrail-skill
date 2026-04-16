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
  "executionToken": "<executionToken>",
  "inputs": {
    "<inputName>": "<inputValue>"
  },
  "transport": {
    "resolve": {
      "method": "POST",
      "path": "/runrail/agent/resolve",
      "body": {}
    },
    "start": {
      "method": "POST",
      "path": "/runrail/agent/start",
      "body": {
        "inputs": {
          "<inputName>": "<inputValue>"
        }
      }
    }
  }
}
```

Legacy fallback format:

```text
executionToken: <executionToken>
```

## Core Rule

Execution mode is strict.

- The API-defined playbook is authoritative.
- The published input list is authoritative for validation and variable resolution.
- The payload `inputs` object is authoritative for runtime values when it is present.
- The published `stepRecords` sequence is authoritative.
- The published step prompt is authoritative.
- The published output exposure rules are authoritative.
- If something required by the API payload is missing, inconsistent, or not executable, stop and say exactly what is wrong.
- Do not switch into redesign, optimization, or advisory mode unless the user explicitly asks for it.

## Mode Selection

- If the user provides `executionToken`, enter execution mode and prioritize the API payload over general workflow advice.
- If the user provides a JSON payload with `kind: "runrail-agent-execution"`, parse `executionToken` from that JSON field exactly. Do not retype, shorten, normalize, or infer the token from surrounding prose.
- If that JSON payload also includes `inputs`, use those `inputs` exactly as the runtime inputs. Do not ask the user to re-enter them.
- If that JSON payload includes `transport`, treat the `transport` block as the authoritative request contract for `resolve` and `start`.
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
6. If the incoming execution payload already includes `inputs`, use those values exactly as provided.
7. When `transport.start.body.inputs` is present, send that inputs payload unchanged in `POST /runrail/agent/start`.
8. Only ask the user for inputs if the execution payload does not include runtime `inputs` and the resolved playbook still requires them.
9. Create the run with a dedicated API call after the runtime inputs are fully known and before executing the first step.
10. Save the returned `runId` and reuse that exact `runId` for all later reporting calls.
11. Do not start the first step until the run has been created and all required inputs are available.
12. Preserve the `running` transition for each step. If you batch reports, include the `running` update before that step's terminal update in the same ordered batch.
13. Execute exactly one published step at a time.
14. After each step finishes, preserve that exact step result before moving to the next step. You may batch consecutive step updates into one request as long as they stay in order.
15. A report request may contain one or more ordered step updates.
16. Every step report must include `step.id`, `step.index`, or `step.title`. Prefer `step.id`.
17. Do not send run-level `status: "running"` in `/report`. Use `step.status` instead.
18. Do not report `step.status` as `pending`. `pending` is the initial server-owned state and is not a valid agent report.
19. Use only the status transitions allowed by `executionProtocol` and the API. In the current strict mode that means `pending -> running -> completed|failed`.
20. Do not report `waiting` or `needs_review` in strict agent execution mode unless the API explicitly allows those transitions.
21. If a step fails, report the failure on that same run and stop.
22. Only after the last published step is complete, report the run as `completed` or `failed`. You may send that final run status in the same request that completes the last remaining step, or in a separate final run-status request.
23. After the final run-status request or combined final batch, call `GET /runrail/agent/runs/<runId>` and verify the persisted state before claiming success.
24. If the verification response does not match the reports you believe you sent, do not claim completion. Continue reconciling or state the mismatch clearly.
25. Do not add commentary that changes the route of execution unless the user explicitly asks for analysis.
26. Do not call the internal one-shot execution endpoint while in strict agent execution mode.
27. For timeline fidelity, include the exact step input context in report updates whenever you have it. Prefer `step.resolvedPrompt` and you may also include `step.inputPreview` or `step.input`.
28. If you resolved the step prompt locally before calling the model, report that exact rendered prompt back to `/report` instead of relying on the server to reconstruct it later.

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

When the payload includes a `transport` block:

- Use `transport.baseUrl` as the base URL when present.
- Use `transport.resolve` literally for the resolve request.
- Use `transport.start` literally for the start request.
- Preserve placeholder substitution such as `Authorization: Bearer <executionToken>`.
- Do not rewrite `transport.start.body.inputs`. Send those runtime inputs unchanged.

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
{"steps":[{"id":"<step1Id>","status":"running"},{"id":"<step1Id>","status":"completed","output":"<step 1 output>"},{"id":"<step2Id>","status":"running"},{"id":"<step2Id>","status":"completed","output":"<step 2 output>"}]}
```

```json
{"steps":[{"id":"<lastStepId>","status":"running"},{"id":"<lastStepId>","status":"completed","output":"<last step output>"}],"status":"completed"}
```

```json
{"status":"completed"}
```

Recommended higher-fidelity step report payloads:

```json
{"step":{"id":"<stepId>","status":"running","resolvedPrompt":"<exact rendered prompt sent to the model>","inputPreview":"<short preview of the step input context>"}}
```

```json
{"step":{"id":"<stepId>","status":"completed","resolvedPrompt":"<exact rendered prompt sent to the model>","inputPreview":"<short preview of the step input context>","output":"<step output>"}}
```

```json
{"step":{"id":"<stepId>","status":"failed","resolvedPrompt":"<exact rendered prompt sent to the model>","inputPreview":"<short preview of the step input context>","error":{"message":"<error message>"}}}
```

These extra fields are recommended for observability and UI accuracy, not a license to change the route or mutate the published prompt.

## Resolved Payload Contract

When the resolve API returns a payload like this, interpret it literally:

- `inputs` is the authoritative input list. Each entry may arrive as a compact tuple like `[name, type, example]`.
- `stepRecords` contains the executable step definitions.
- `executionProtocol` is the authoritative route contract for runtime execution and reporting.
- Each `stepRecords` item carries the fields that matter for execution, including `idPost`, `name`, `prompt`, `outputKey`, and `exposeAsOutput`.
- `steps` may appear as a lightweight list of step ids. Use it only to confirm the same route published in `stepRecords`, not to invent a second execution model.
- If `steps` references an id that is missing from `stepRecords`, stop and report that exact missing step id.
- If `stepRecords` is empty, say plainly that there are no executable steps.

When the incoming execution payload already includes runtime values:

- `payload.inputs` is the authoritative input-value object for this run.
- Those input values should already reflect what the user entered in the product.
- Use them to resolve `{{input.foo}}` and `{{inputs.foo}}`.
- Do not rename keys, trim values, coerce types, or normalize field names unless the API explicitly requires it.
- If `payload.inputs` and `transport.start.body.inputs` are both present and differ, stop and report the mismatch instead of guessing.

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
- If the execution payload already includes `inputs`, do not ask the user any input questions.
- Reuse `payload.inputs` exactly as the run inputs for this execution.
- If `transport.start.body.inputs` is present, send it unchanged.
- If there are no inputs, state that clearly and continue.
- If inputs arrive as tuples, interpret them as `name`, `type`, `example`.
- Ask for one input at a time only when runtime values were not already supplied in the execution payload.
- When there are multiple required inputs and you truly need to ask for them, label each question as `current/total`.
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
- You may send more than one step update in a single report request only when the updates stay strictly ordered and preserve every allowed transition.
- Do not omit the step identifier in a report. Prefer `step.id` over `step.title`.
- Do not report a later step before the payload reflects the earlier transition in the same ordered batch or a previous successful API response.
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
