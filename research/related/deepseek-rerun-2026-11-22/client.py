#!/usr/bin/env python3
"""DeepSeek chat client for the 2026-11-22 model/thinking rerun.

Reads DEEPSEEK_API_KEY only at request time. Never writes the key to disk,
logs, or return values. Thinking is set explicitly per arm:

  R1/R2: thinking.type=disabled, temperature is sent
  R3:    thinking.type=enabled, reasoning_effort=high, no temperature

Docs: https://api-docs.deepseek.com/ and the Thinking Mode guide.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any, Optional

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODELS_URL = "https://api.deepseek.com/models"

# Real key shape from the task: sk- + a long hex string.
# Also compare the literal env value. Do not print either.
HEX_KEY_RE = re.compile(r"(?<![A-Za-z0-9])sk-[0-9a-fA-F]{16,}")

ARMS = {
    "R1": {
        "model": "deepseek-flash",
        "thinking": {"type": "disabled"},
        "reasoning_effort": None,
        "send_temperature": True,
        "max_tokens": 2000,
        "timeout_s": 180,
    },
    "R2": {
        "model": "deepseek-v4-pro",
        "thinking": {"type": "disabled"},
        "reasoning_effort": None,
        "send_temperature": True,
        "max_tokens": 2000,
        "timeout_s": 300,
    },
    "R3": {
        "model": "deepseek-flash",
        "thinking": {"type": "enabled"},
        "reasoning_effort": "high",
        "send_temperature": False,
        # Thinking tokens count toward max_tokens (API docs). 2000 would
        # risk truncating content; this is the only client-budget change
        # vs PR #57/#58, and applies only to R3.
        "max_tokens": 16384,
        "timeout_s": 600,
    },
}


def redact(text: str) -> str:
    if text is None:
        return text
    out = str(text)
    key = os.environ.get("DEEPSEEK_API_KEY") or ""
    if key:
        out = out.replace(key, "[REDACTED]")
    out = HEX_KEY_RE.sub("[REDACTED]", out)
    return out


def contains_secret(text: str) -> bool:
    key = os.environ.get("DEEPSEEK_API_KEY") or ""
    if key and key in (text or ""):
        return True
    return bool(HEX_KEY_RE.search(text or ""))


def build_payload(
    messages: list[dict[str, str]],
    *,
    arm: str,
    temperature: Optional[float] = None,
) -> dict[str, Any]:
    if arm not in ARMS:
        raise ValueError(f"unknown arm: {arm}")
    cfg = ARMS[arm]
    payload: dict[str, Any] = {
        "model": cfg["model"],
        "messages": messages,
        "max_tokens": cfg["max_tokens"],
        "stream": False,
        "thinking": dict(cfg["thinking"]),
    }
    if cfg["reasoning_effort"]:
        payload["reasoning_effort"] = cfg["reasoning_effort"]
    if cfg["send_temperature"]:
        if temperature is None:
            raise ValueError(f"{arm} requires temperature")
        payload["temperature"] = temperature
    return payload


def _error_payload(exc: BaseException) -> dict[str, Any]:
    info: dict[str, Any] = {
        "type": type(exc).__name__,
        "message": redact(str(exc)),
    }
    if isinstance(exc, urllib.error.HTTPError):
        info["http_status"] = exc.code
        info["http_reason"] = redact(getattr(exc, "reason", "") or "")
        try:
            body = exc.read()
            info["body"] = redact(body.decode("utf-8", errors="replace")[:4000])
        except Exception as read_exc:  # noqa: BLE001
            info["body_read_error"] = type(read_exc).__name__
    elif isinstance(exc, urllib.error.URLError):
        info["reason"] = redact(str(getattr(exc, "reason", exc)))
    return info


def _usage(body: dict) -> dict[str, Any]:
    usage = body.get("usage") if isinstance(body, dict) else None
    if not isinstance(usage, dict):
        return {}
    return json.loads(redact(json.dumps(usage, ensure_ascii=False)))


def deepseek_chat(
    messages: list[dict[str, str]],
    *,
    arm: str,
    temperature: Optional[float] = None,
) -> dict[str, Any]:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not set in the environment")
    cfg = ARMS[arm]
    payload = build_payload(messages, arm=arm, temperature=temperature)
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        DEEPSEEK_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    del api_key

    try:
        with urllib.request.urlopen(request, timeout=cfg["timeout_s"]) as resp:
            status = getattr(resp, "status", 200)
            raw = resp.read()
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": _error_payload(exc),
            "request_payload_meta": {
                "model": payload["model"],
                "thinking": payload.get("thinking"),
                "reasoning_effort": payload.get("reasoning_effort"),
                "temperature_sent": "temperature" in payload,
                "temperature": payload.get("temperature"),
                "max_tokens": payload.get("max_tokens"),
                "url": DEEPSEEK_URL,
                "arm": arm,
            },
        }
    finally:
        request.headers = {}
        if hasattr(request, "unredirected_hdrs"):
            request.unredirected_hdrs = {}

    text = redact(raw.decode("utf-8", errors="replace"))
    try:
        body = json.loads(text)
    except json.JSONDecodeError as exc:
        return {
            "ok": False,
            "error": {
                "type": "JSONDecodeError",
                "message": redact(str(exc)),
                "http_status": status,
                "body_prefix": text[:500],
            },
        }

    body = json.loads(redact(json.dumps(body, ensure_ascii=False)))
    choice = {}
    if isinstance(body, dict) and body.get("choices"):
        choice = body["choices"][0] or {}
    message = (choice.get("message") or {}) if isinstance(choice, dict) else {}
    content = message.get("content") if isinstance(message, dict) else None
    reasoning = None
    if isinstance(message, dict):
        if "reasoning_content" in message:
            reasoning = message.get("reasoning_content")
        elif "reasoning" in message and message.get("reasoning") not in (None, ""):
            reasoning = message.get("reasoning")

    usage = _usage(body) if isinstance(body, dict) else {}
    return {
        "ok": True,
        "http_status": status,
        "arm": arm,
        "model_requested": payload["model"],
        "model": body.get("model") if isinstance(body, dict) else payload["model"],
        "id": body.get("id") if isinstance(body, dict) else None,
        "content": content,
        "reasoning_content": reasoning,
        "has_reasoning_content": bool(reasoning),
        "finish_reason": choice.get("finish_reason") if isinstance(choice, dict) else None,
        "usage": usage,
        "thinking_requested": payload.get("thinking"),
        "reasoning_effort_requested": payload.get("reasoning_effort"),
        "temperature_sent": payload.get("temperature"),
        "max_tokens": payload.get("max_tokens"),
        "raw_response": body,
    }
