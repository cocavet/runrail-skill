#!/usr/bin/env python3

import argparse
import json
import subprocess
import sys
import time


APP_BASE = "https://app.runrail.io"
SPINNER_WIDTH = 15
POLL_INTERVAL_SECONDS = 0.12


def parse_args():
    parser = argparse.ArgumentParser(
        description="Resolve a RunRail playbook with a single execution token."
    )
    parser.add_argument("--execution-token", required=True)
    return parser.parse_args()


def build_spinner_frames(width):
    frames = []
    for filled in range(1, width + 1):
        frames.append("[" + ("#" * filled).ljust(width, ".") + "]")
    for filled in range(width - 1, 0, -1):
        frames.append("[" + ("#" * filled).ljust(width, ".") + "]")
    return tuple(frames)


SPINNER_FRAMES = build_spinner_frames(SPINNER_WIDTH)


def clear_status_line(width):
    sys.stderr.write("\r" + (" " * width) + "\r")
    sys.stderr.flush()


def missing_playbook_message(payload):
    default_message = "No playbook data found for the provided execution token."

    if payload in (None, {}, []):
        return default_message

    if isinstance(payload, dict):
        if "playbook" in payload and payload["playbook"] in (None, {}, []):
            return payload.get("message") or default_message
        if "resolvedPlaybook" in payload and payload["resolvedPlaybook"] in (None, {}, []):
            return payload.get("message") or default_message
        if set(payload.keys()).issubset({"message", "error", "status", "statusCode"}):
            return payload.get("message") or payload.get("error") or default_message

    return None


def main():
    args = parse_args()

    command = [
        "curl",
        "-sS",
        "--max-time",
        "30",
        "-X",
        "POST",
        f"{APP_BASE}/api/runrail/agent/resolve",
        "-H",
        f"Authorization: Bearer {args.execution_token}",
        "-H",
        "Content-Type: application/json",
        "-d",
        json.dumps({}),
    ]

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    status_width = len(f"Connecting {SPINNER_FRAMES[0]}")
    frame_index = 0
    sys.stderr.write(f"\rConnecting {SPINNER_FRAMES[frame_index]}")
    sys.stderr.flush()
    frame_index += 1
    while process.poll() is None:
        sys.stderr.write(f"\rConnecting {SPINNER_FRAMES[frame_index % len(SPINNER_FRAMES)]}")
        sys.stderr.flush()
        frame_index += 1
        time.sleep(POLL_INTERVAL_SECONDS)

    stdout, stderr = process.communicate()
    clear_status_line(status_width)

    if process.returncode != 0:
        message = stderr.strip() or "curl request failed"
        sys.stderr.write(f"{message}\n")
        return 1

    stripped_stdout = stdout.strip()
    if not stripped_stdout:
        sys.stderr.write("No playbook data found for the provided execution token.\n")
        return 1

    try:
        payload = json.loads(stripped_stdout)
    except json.JSONDecodeError:
        payload = None

    missing_message = missing_playbook_message(payload) if payload is not None else None
    if missing_message:
        sys.stderr.write(f"{missing_message}\n")
        return 1

    sys.stdout.write(stdout)
    if stdout and not stdout.endswith("\n"):
        sys.stdout.write("\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
