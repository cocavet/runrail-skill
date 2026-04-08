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

## Repo Layout

```text
runrail-skill/
  README.md
  runrail/
    SKILL.md
    agents/
      openai.yaml
```
