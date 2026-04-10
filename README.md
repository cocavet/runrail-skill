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

- Reuse the exact `runId` returned by `POST /runrail/agent/start`.
- Send exactly one step update per `POST /runrail/agent/runs/<runId>/report`.
- Include `step.id`, `step.index`, or `step.title` in every step report. Prefer `step.id`.
- Do not send run-level `status: "running"` in `/report`.
- Send the final run status in a separate request only after all steps are reported.

## Repo Layout

```text
runrail-skill/
  README.md
  runrail/
    SKILL.md
    agents/
      openai.yaml
```
