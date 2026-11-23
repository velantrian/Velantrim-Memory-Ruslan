#!/usr/bin/env python3
"""OpenRouter chat client for the 2026-11-23 control-model run.

Reads OPENROUTER_API_KEY only at request time. Never writes the key to
disk, logs, or return values.

Arms:
  luna      — openai/gpt-6-luna, reasoning.effort=high, temperature sent
  nemotron  — nvidia/nemotron-3-ultra-550b-a55b (paid id, not :free),
              no reasoning.effort, temperature sent

Luna uses a larger max_tokens because OpenRouter allocates ~80% of
max_tokens to reasoning when effort=high; 2000 would risk truncating
content (same rationale as PR #59 R3).
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any, Optional

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# OpenRouter keys are sk-or-… ; also redact a live env value and a long hex sk-.
OR_KEY_RE = re.compile(r"sk-or-[A-Za-z0-9_-]{8,}")
HEX_KEY_RE = re.compile(r"(?<![A-Za-z0-9])sk-[0-9a-fA-F]{16,}")

ARMS = {
    "luna": {
        "model": "openai/gpt-6-luna",
        "reasoning": {"effort": "high"},
        "send_temperature": True,
        "max_tokens": 16384,
        "timeout_s": 600,
    },
    "nemotron": {
        "model": "nvidia/nemotron-3-ultra-550b-a55b",
        "reasoning": None,
        "send_temperature": True,
        # Canary (paid id) returned reasoning_content even without
        # reasoning.effort; 2000 would risk truncating the official draft.
        # 16384 is the same client-budget choice as Luna / PR #59 R3.
        "max_tokens": 16384,
        "timeout_s": 600,
    },
}


def _secrets() -> list[str]:
    out = []
    for name in ("OPENROUTER_API_KEY", "DEEPSEEK_API_KEY"):
        val = os.environ.get(name) or ""
        if val:
            out.append(val)
    return out


def redact(text: str) -> str:
    if text is None:
        return text
    out = str(text)
    for key in _secrets():
        out = out.replace(key, "[REDACTED]")
    out = OR_KEY_RE.sub("[REDACTED]", out)
    out = HEX_KEY_RE.sub("[REDACTED]", out)
    return out


def contains_secret(text: str) -> bool:
    blob = text or ""
    for key in _secrets():
        if key and key in blob:
            return True
    if OR_KEY_RE.search(blob):
        return True
    return bool(HEX_KEY_RE.search(blob))


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
    }
    if cfg["reasoning"] is not None:
        payload["reasoning"] = dict(cfg["reasoning"])
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


def extract_reasoning(message: dict) -> Optional[str]:
    """Collect provider reasoning text, if any, without using it for scoring."""
    if not isinstance(message, dict):
        return None
    parts: list[str] = []
    for key in ("reasoning_content", "reasoning"):
        val = message.get(key)
        if val in (None, "", [], {}):
            continue
        if isinstance(val, str):
            parts.append(val)
        else:
            parts.append(json.dumps(val, ensure_ascii=False))
    details = message.get("reasoning_details")
    if details not in (None, "", [], {}):
        if isinstance(details, str):
            parts.append(details)
        else:
            parts.append(json.dumps(details, ensure_ascii=False))
    text = "\n".join(parts).strip()
    return text or None


def openrouter_chat(
    messages: list[dict[str, str]],
    *,
    arm: str,
    temperature: Optional[float] = None,
) -> dict[str, Any]:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set in the environment")
    cfg = ARMS[arm]
    payload = build_payload(messages, arm=arm, temperature=temperature)
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        OPENROUTER_URL,
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
                "reasoning": payload.get("reasoning"),
                "temperature_sent": "temperature" in payload,
                "temperature": payload.get("temperature"),
                "max_tokens": payload.get("max_tokens"),
                "url": OPENROUTER_URL,
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
    # OpenRouter error objects sometimes come with HTTP 200.
    if isinstance(body, dict) and body.get("error"):
        return {
            "ok": False,
            "http_status": status,
            "error": {
                "type": "OpenRouterError",
                "message": redact(json.dumps(body.get("error"), ensure_ascii=False)[:4000]),
            },
            "request_payload_meta": {
                "model": payload["model"],
                "reasoning": payload.get("reasoning"),
                "temperature": payload.get("temperature"),
                "max_tokens": payload.get("max_tokens"),
                "url": OPENROUTER_URL,
                "arm": arm,
            },
        }

    choice = {}
    if isinstance(body, dict) and body.get("choices"):
        choice = body["choices"][0] or {}
    message = (choice.get("message") or {}) if isinstance(choice, dict) else {}
    content = message.get("content") if isinstance(message, dict) else None
    # Some providers return a list of content parts.
    if isinstance(content, list):
        chunks = []
        for part in content:
            if isinstance(part, str):
                chunks.append(part)
            elif isinstance(part, dict) and part.get("type") in (None, "text"):
                chunks.append(str(part.get("text") or part.get("content") or ""))
        content = "".join(chunks)
    reasoning = extract_reasoning(message) if isinstance(message, dict) else None
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
        "native_finish_reason": choice.get("native_finish_reason") if isinstance(choice, dict) else None,
        "usage": usage,
        "cost": usage.get("cost") if isinstance(usage, dict) else None,
        "reasoning_requested": payload.get("reasoning"),
        "temperature_sent": payload.get("temperature"),
        "max_tokens": payload.get("max_tokens"),
        "raw_response": body,
    }
