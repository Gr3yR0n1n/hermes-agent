"""Google Workspace tool — wraps google_api.py for calendar, gmail, and drive access."""

import json
import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

SCHEMA = {
    "name": "google_workspace",
    "description": (
        "Access Google Workspace (Calendar, Gmail, Drive) "
        "Use service='calendar' with actions: list, create, accept, delete. "
        "Use service='gmail' with actions: search, get, send, reply. "
        "Use service='drive' with actions: search."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "service": {
                "type": "string",
                "enum": ["calendar", "gmail", "drive"],
                "description": "Which Google service to use.",
            },
            "action": {
                "type": "string",
                "description": (
                    "calendar: list, create, accept, delete. "
                    "gmail: search, get, send, reply. "
                    "drive: search."
                ),
            },
            "args": {
                "type": "object",
                "description": (
                    "Arguments for the action. Examples:\n"
                    "calendar list: {start: '2026-05-01T00:00:00', end: '2026-05-07T23:59:59'}\n"
                    "calendar accept: {event_id: 'abc123'}\n"
                    "calendar create: {summary: 'Title', start: '2026-05-01T10:00:00', end: '2026-05-01T11:00:00'}\n"
                    "calendar delete: {event_id: 'abc123'}\n"
                    "gmail search: {query: 'is:unread', max: 10}\n"
                    "gmail get: {message_id: 'abc123'}\n"
                    "gmail send: {to: 'user@example.com', subject: 'Hi', body: 'Hello'}\n"
                    "gmail reply: {message_id: 'abc123', body: 'Thanks'}\n"
                    "drive search: {query: 'budget report'}"
                ),
            },
        },
        "required": ["service", "action", "args"],
    },
}


def _gapi_python() -> str:
    venv = Path.home() / ".hermes" / "hermes-agent" / ".venv" / "bin" / "python3"
    if venv.exists():
        return str(venv)
    return sys.executable


def _gapi_script() -> str:
    return str(
        Path.home()
        / ".hermes"
        / "hermes-agent"
        / "skills"
        / "productivity"
        / "google-workspace"
        / "scripts"
        / "google_api.py"
    )


def _build_cmd(service: str, action: str, args: dict) -> list[str]:
    cmd = [_gapi_python(), _gapi_script(), service, action]
    a = args or {}

    # calendar list
    if service == "calendar" and action == "list":
        if a.get("start"):
            cmd += ["--start", a["start"]]
        if a.get("end"):
            cmd += ["--end", a["end"]]
        if a.get("calendar"):
            cmd += ["--calendar", a["calendar"]]

    # calendar accept
    elif service == "calendar" and action == "accept":
        cmd.append(a["event_id"])
        if a.get("calendar"):
            cmd += ["--calendar", a["calendar"]]

    # calendar create
    elif service == "calendar" and action == "create":
        cmd += ["--summary", a["summary"], "--start", a["start"], "--end", a["end"]]
        if a.get("location"):
            cmd += ["--location", a["location"]]
        if a.get("description"):
            cmd += ["--description", a["description"]]
        if a.get("attendees"):
            cmd += ["--attendees", a["attendees"]]

    # calendar delete
    elif service == "calendar" and action == "delete":
        cmd.append(a["event_id"])

    # gmail search
    elif service == "gmail" and action == "search":
        cmd.append(a.get("query", "is:unread"))
        if a.get("max"):
            cmd += ["--max", str(a["max"])]

    # gmail get
    elif service == "gmail" and action == "get":
        cmd.append(a["message_id"])

    # gmail send
    elif service == "gmail" and action == "send":
        cmd += ["--to", a["to"], "--subject", a["subject"], "--body", a["body"]]
        if a.get("cc"):
            cmd += ["--cc", a["cc"]]
        if a.get("thread_id"):
            cmd += ["--thread-id", a["thread_id"]]

    # gmail reply
    elif service == "gmail" and action == "reply":
        cmd += [a["message_id"], "--body", a["body"]]

    # drive search
    elif service == "drive" and action == "search":
        cmd.append(a.get("query", ""))
        if a.get("max"):
            cmd += ["--max", str(a["max"])]

    return cmd


def google_workspace(service: str, action: str, args: dict) -> str:
    try:
        cmd = _build_cmd(service, action, args)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return json.dumps({"error": result.stderr.strip() or "command failed"})
        output = result.stdout.strip()
        try:
            return json.dumps(json.loads(output), ensure_ascii=False)
        except json.JSONDecodeError:
            return json.dumps({"result": output})
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "google_api.py timed out after 30s"})
    except Exception as exc:
        logger.exception("google_workspace tool failed")
        return json.dumps({"error": str(exc)})


# ── Registration ──────────────────────────────────────────────────────────────

from tools.registry import registry

registry.register(
    name="google_workspace",
    toolset="core",
    schema=SCHEMA,
    handler=lambda args, **kw: google_workspace(
        service=args["service"],
        action=args["action"],
        args=args.get("args", {}),
    ),
    emoji="📅",
)
