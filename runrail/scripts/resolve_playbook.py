#!/usr/bin/env python3

import argparse
import json
import subprocess
import sys


APP_BASE = "https://app.runrail.io"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Resolve a RunRail playbook with a single API call."
    )
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--playbook-id", required=True)
    parser.add_argument("--api-key", required=True)
    return parser.parse_args()


def main():
    args = parse_args()

    command = [
        "curl",
        "-sS",
        "--max-time",
        "30",
        "-X",
        "POST",
        f"{APP_BASE}/api/runrail/playbooks/resolve",
        "-H",
        f"Authorization: Bearer {args.api_key}",
        "-H",
        "Content-Type: application/json",
        "-d",
        json.dumps(
            {
                "projectId": args.project_id,
                "playbookId": args.playbook_id,
            }
        ),
    ]

    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        message = result.stderr.strip() or "curl request failed"
        raise RuntimeError(message)

    sys.stdout.write(result.stdout)
    if result.stdout and not result.stdout.endswith("\n"):
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
