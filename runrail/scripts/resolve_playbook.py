#!/usr/bin/env python3

import argparse
import json
import subprocess
import sys


APP_BASE = "https://app.runrail.io"
DEFAULT_INPUT_TYPE = "text"


def to_text(value):
    if value is None:
        return ""
    return str(value)


def scalar_id(value):
    if isinstance(value, list):
        if not value:
            return ""
        return scalar_id(value[0])
    return to_text(value).strip()


def first_item(value):
    if isinstance(value, list):
        return value[0] if value else None
    return value


def truthy(value):
    return value is True or value == "true" or value == 1 or value == "1"


def post_json(url, payload, api_key):
    command = [
        "curl",
        "-sS",
        "--max-time",
        "30",
        "-X",
        "POST",
        url,
        "-H",
        f"Authorization: Bearer {api_key}",
        "-H",
        "Content-Type: application/json",
        "-d",
        json.dumps(payload),
        "-w",
        "\n__HTTP_STATUS__:%{http_code}\n",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    output = result.stdout

    if "__HTTP_STATUS__:" not in output:
        message = result.stderr.strip() or "curl did not return an HTTP status marker"
        raise RuntimeError(message)

    body, status_text = output.rsplit("\n__HTTP_STATUS__:", 1)
    try:
        status = int(status_text.strip())
    except ValueError as error:
        raise RuntimeError(f"could not parse HTTP status from curl output: {status_text!r}") from error

    return status, body


def query_orbbe(query, options, api_key):
    status, body = post_json(
        f"{APP_BASE}/api/orbbe",
        {"query": query, "options": options},
        api_key,
    )
    if status != 200:
        raise RuntimeError(f"orbbe query {query!r} failed with HTTP {status}: {body}")

    payload = json.loads(body)
    if payload.get("statusCode") != 200:
        raise RuntimeError(
            f"orbbe query {query!r} failed with statusCode {payload.get('statusCode')}: "
            f"{payload.get('message', '')}"
        )
    return payload.get("data")


def normalize_input(item, index):
    if isinstance(item, list):
        name = to_text(item[0] if len(item) > 0 else "").strip()
        input_type = to_text(item[1] if len(item) > 1 else DEFAULT_INPUT_TYPE).strip() or DEFAULT_INPUT_TYPE
        example = to_text(item[2] if len(item) > 2 else "")
        return {
            "id": f"input_{index + 1}",
            "name": name,
            "type": input_type,
            "example": example,
            "required": True,
        }

    if not isinstance(item, dict):
        return None

    return {
        "id": to_text(item.get("id") or item.get("name") or f"input_{index + 1}"),
        "name": to_text(item.get("name")).strip(),
        "type": to_text(item.get("type") or DEFAULT_INPUT_TYPE).strip() or DEFAULT_INPUT_TYPE,
        "example": to_text(item.get("example") or item.get("placeholder")),
        "required": item.get("required") is not False,
    }


def normalize_inputs(items):
    if not isinstance(items, list):
        return []
    normalized = []
    for index, item in enumerate(items):
        value = normalize_input(item, index)
        if value:
            normalized.append(value)
    return normalized


def normalize_step(item, index):
    if not isinstance(item, dict):
        return None

    return {
        "id": to_text(item.get("idPost") or item.get("id") or f"step_{index + 1}"),
        "title": to_text(item.get("title") or item.get("name") or f"Step {index + 1}").strip()
        or f"Step {index + 1}",
        "prompt": to_text(item.get("prompt") or item.get("instructions")),
        "outputKey": to_text(item.get("outputKey")).strip(),
        "exposeAsOutput": truthy(item.get("exposeAsOutput")),
        "index": index,
        "source": item,
    }


def normalize_steps(items):
    if not isinstance(items, list):
        return []
    normalized = []
    for index, item in enumerate(items):
        value = normalize_step(item, index)
        if value:
            normalized.append(value)
    return normalized


def order_step_records(step_records, ordered_ids):
    if not step_records:
        return []
    if not ordered_ids:
        return list(step_records)

    by_id = {scalar_id(item.get("idPost") or item.get("id")): item for item in step_records}
    ordered = []
    seen = set()

    for step_id in ordered_ids:
        if not step_id or step_id in seen:
            continue
        record = by_id.get(step_id)
        if record:
            ordered.append(record)
            seen.add(step_id)

    for item in step_records:
        step_id = scalar_id(item.get("idPost") or item.get("id"))
        if not step_id or step_id in seen:
            continue
        ordered.append(item)
        seen.add(step_id)

    return ordered


def extract_step_order(items):
    if not isinstance(items, list):
        return []
    ordered = []
    seen = set()
    for item in items:
        step_id = scalar_id(item)
        if not step_id or step_id in seen:
            continue
        ordered.append(step_id)
        seen.add(step_id)
    return ordered


def pick_playbook_candidate(payload):
    if isinstance(payload, dict):
        candidate = payload.get("playbook") or payload.get("resolvedPlaybook")
        if isinstance(candidate, list):
            candidate = first_item(candidate)
        if isinstance(candidate, dict):
            return candidate

        keys = {"description", "globalInstructions", "inputs", "steps", "name", "titlePost"}
        if keys.intersection(payload.keys()):
            return payload

        for value in payload.values():
            candidate = pick_playbook_candidate(value)
            if candidate:
                return candidate
    elif isinstance(payload, list):
        for value in payload:
            candidate = pick_playbook_candidate(value)
            if candidate:
                return candidate
    return None


def pick_steps_candidate(payload, playbook):
    if isinstance(payload, dict):
        if isinstance(payload.get("stepRecords"), list):
            return payload["stepRecords"]
        steps = payload.get("steps")
        if isinstance(steps, list) and steps and isinstance(first_item(steps), dict):
            return steps
        for value in payload.values():
            candidate = pick_steps_candidate(value, playbook)
            if candidate is not None:
                return candidate

    if isinstance(playbook, dict):
        if isinstance(playbook.get("stepRecords"), list):
            return playbook["stepRecords"]
        steps = playbook.get("steps")
        if isinstance(steps, list) and steps and isinstance(first_item(steps), dict):
            return steps

    return None


def build_output(project_id, playbook_id, source, playbook, step_records, resolve_meta=None):
    ordered_ids = extract_step_order(playbook.get("steps")) if isinstance(playbook, dict) else []
    ordered_records = order_step_records(step_records, ordered_ids)

    return {
        "projectId": project_id,
        "playbookId": playbook_id,
        "source": source,
        "resolve": resolve_meta or {},
        "name": to_text(playbook.get("name") or playbook.get("titlePost")) if isinstance(playbook, dict) else "",
        "description": to_text(playbook.get("description")) if isinstance(playbook, dict) else "",
        "globalInstructions": to_text(playbook.get("globalInstructions")) if isinstance(playbook, dict) else "",
        "executionType": to_text(playbook.get("executionType")) if isinstance(playbook, dict) else "",
        "versionNumber": to_text(playbook.get("versionNumber")) if isinstance(playbook, dict) else "",
        "inputs": normalize_inputs(playbook.get("inputs") if isinstance(playbook, dict) else []),
        "steps": normalize_steps(ordered_records),
    }


def try_resolve(project_id, playbook_id, api_key):
    status, body = post_json(
        f"{APP_BASE}/runrail/playbooks/resolve",
        {"projectId": project_id, "playbookId": playbook_id},
        api_key,
    )
    if status != 200:
        raise RuntimeError(f"resolve endpoint returned HTTP {status}: {body}")

    payload = json.loads(body)
    data = payload.get("data", payload) if isinstance(payload, dict) else payload
    playbook = pick_playbook_candidate(data)
    if not isinstance(playbook, dict):
        raise RuntimeError("resolve endpoint returned JSON, but no playbook object could be identified")

    step_records = pick_steps_candidate(data, playbook) or []
    return build_output(
        project_id,
        playbook_id,
        "resolve",
        playbook,
        step_records,
        resolve_meta={"used": True, "status": "ok"},
    )


def fallback_orbbe(project_id, playbook_id, api_key, resolve_error):
    playbook = first_item(
        query_orbbe(
            "getPlaybook",
            {"idPost": playbook_id, "language": "default"},
            api_key,
        )
    )
    source = "fallback-orbbe:getPlaybook"

    if not isinstance(playbook, dict):
        playbook = first_item(
            query_orbbe(
                "getVersion",
                {"idPost": playbook_id, "language": "default"},
                api_key,
            )
        )
        source = "fallback-orbbe:getVersion"

    if not isinstance(playbook, dict):
        raise RuntimeError("could not load the playbook with getPlaybook or getVersion")

    step_owner_id = scalar_id(playbook.get("idPost") or playbook_id)
    step_records = query_orbbe(
        "getSteps",
        {"relatedPost": step_owner_id, "createdAt": None, "language": "default"},
        api_key,
    )
    if not isinstance(step_records, list):
        step_records = []

    return build_output(
        project_id,
        playbook_id,
        source,
        playbook,
        step_records,
        resolve_meta={"used": False, "status": "fallback", "error": resolve_error},
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Resolve a Runrail playbook using the public resolve endpoint with an internal fallback."
    )
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--playbook-id", required=True)
    parser.add_argument("--api-key", required=True)
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        result = try_resolve(args.project_id, args.playbook_id, args.api_key)
    except Exception as error:
        result = fallback_orbbe(args.project_id, args.playbook_id, args.api_key, str(error))

    json.dump(result, sys.stdout, indent=2, ensure_ascii=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
