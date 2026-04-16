# Strict Execution Contract

Read this file only when the user supplies an `executionToken` or a payload with `kind: "runrail-agent-execution"`.

## Source of Truth

- The resolved playbook payload is authoritative.
- The published inputs list is authoritative for validation and variable resolution.
- `payload.inputs` is authoritative for runtime values when present.
- `transport` is authoritative when present.
- `stepRecords` is the executable step sequence.
- `executionProtocol` is the runtime contract.

## Mode Rules

- Parse `executionToken` exactly as provided.
- If payload `inputs` exist, use them exactly and do not ask again.
- If `payload.inputs` and `transport.start.body.inputs` both exist and differ, stop and report the mismatch.
- Do not switch into redesign or optimization unless the user explicitly asks.

## API Route

Use only this path in strict execution mode:

1. `POST /runrail/agent/resolve`
2. `POST /runrail/agent/start`
3. `POST /runrail/agent/runs/<runId>/report`
4. `GET /runrail/agent/runs/<runId>` for verification or reconciliation

Do not use the one-shot playbook run endpoint in strict execution mode.

If `transport` is present:

- use `transport.baseUrl` when provided
- use `transport.resolve` literally
- use `transport.start` literally
- preserve placeholder auth/header values
- send `transport.start.body.inputs` unchanged when present

## Required Execution Order

1. Resolve first.
2. Read `description`, `globalInstructions`, `inputs`, `steps`, `stepRecords`, and `executionProtocol`.
3. Ask for inputs only if runtime values were not already supplied and the resolved playbook still requires them.
4. Start the run only after required inputs are known.
5. Save the returned `runId` and reuse that exact id for all reports.
6. Execute exactly one published step at a time.
7. Preserve each step result before moving on.
8. If a step fails, report that failure on the same run and stop.
9. After the last step, report final run status.
10. Verify persisted run state before claiming completion.

## Reporting Rules

- Every step report must identify the step. Prefer `step.id`.
- Do not report run-level `status: "running"` in `/report`.
- Do not report `step.status: "pending"`.
- Preserve allowed transitions in order: `pending -> running -> completed|failed`.
- You may batch ordered step updates in one report request if the sequence remains correct.
- Do not claim a report succeeded unless the API call succeeded.

Minimum valid report bodies:

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
{"steps":[{"id":"<step1Id>","status":"running"},{"id":"<step1Id>","status":"completed","output":"<step 1 output>"}],"status":"completed"}
```

Recommended observability fields when available:

- `resolvedPrompt`
- `inputPreview`
- `input`

## Inputs And Variables

- Input tuples may arrive as `[name, type, example]`.
- Use `{{input.foo}}` and `{{inputs.foo}}` from runtime inputs.
- Use `{{output.foo}}` and `{{outputs.foo}}` from prior step outputs.
- Ignore harmless whitespace inside placeholders.
- Preserve published input names exactly, including spaces.
- If a referenced variable cannot be resolved, stop and name it exactly.

## Step Execution

- Use `stepRecords` strictly in published order.
- Use the published step name; if missing, fall back to `idPost`.
- If a step prompt is empty, stop and report that the playbook is not executable as published.
- Preserve raw step outputs.
- Store outputs under `outputKey` when present, otherwise use a stable fallback such as `idPost`.
- Surface outputs marked `exposeAsOutput`.
- Do not rewrite a step's intent or silently guess missing data.

## Resolve Helper

Preferred helper:

```bash
python3 scripts/resolve_playbook.py --execution-token "<executionToken>"
```

Equivalent raw request:

```bash
curl -X POST https://app.runrail.io/api/runrail/agent/resolve \
  -H "Authorization: Bearer <executionToken>" \
  -H "Content-Type: application/json" \
  -d '{}'
```
