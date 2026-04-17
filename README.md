# RunRail Skill

Minimal public repo for installing the RunRail skill in Codex.

## Install

Run this in Codex:

```bash
python3 "$HOME/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo cocavet/runrail-skill \
  --path runrail
```

Restart Codex after installation so the new skill is picked up.

## Update

If the skill is already installed, replace the installed copy and reinstall it:

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/runrail"

mv "$SKILL_DIR" "${SKILL_DIR}.bak.$(date +%Y%m%d%H%M%S)"

python3 "$HOME/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo cocavet/runrail-skill \
  --path runrail
```

Restart Codex after updating so the new version is loaded.

## Current Agent Contract

The exported skill now makes the strict `/report` contract explicit for agents:

- Treat the copied execution payload as the runtime source of truth, including `inputs` and `transport`.
- Call `POST /runrail/agent/resolve` first.
- Reuse the provided start `inputs` unchanged when calling `POST /runrail/agent/start`.
- Treat empty input values as optional `null` values during validation and prompt resolution, so they do not block execution or trigger a re-ask.
- Reuse the exact `runId` returned by `POST /runrail/agent/start`.
- You may send one or more ordered step updates per `POST /runrail/agent/runs/<runId>/report`.
- Include `step.id`, `step.index`, or `step.title` in every step report. Prefer `step.id`.
- Do not send run-level `status: "running"` in `/report`.
- Preserve every allowed transition in order when batching, including `running` before `completed` or `failed`.
- Prefer reporting the exact rendered step input back to `/report` with `resolvedPrompt`, and optionally `inputPreview` or `input`, so the execution timeline shows the real input context.
- You may send the final run status in the same request that completes the last step, or in a separate final request after that.

## Repo Layout

```text
runrail-skill/
  README.md
  runrail/
    SKILL.md
    agents/
      openai.yaml
```
