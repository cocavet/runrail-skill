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

## Repo Layout

```text
runrail-skill/
  README.md
  runrail/
    SKILL.md
    agents/
      openai.yaml
```
