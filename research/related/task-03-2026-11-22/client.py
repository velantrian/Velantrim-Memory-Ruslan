#!/usr/bin/env python3
"""DeepSeek chat client for ICT-01.

The API key is read from DEEPSEEK_API_KEY at call time only.
It is never written to disk, logs, or returned structures.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "deepseek-chat"
SK_RE = re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9]{16,}")


def redact(text: str) -> str:
    """Remove any API-key-shaped token from a string. Does not take the key as an argument
    so accidental interpolation is harder; also redacts the runtime key if present.
    """
    if text is None:
        return text
    out = str(text)
    key = os.environ.get("DEEPSEEK_API_KEY") or ""
    if key:
        out = out.replace(key, "[REDACTED]")
    out = SK_RE.sub("[REDACTED]", out)
    return out


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


def deepseek_chat(
    messages: list[dict[str, str]],
    *,
    temperature: float,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 2000,
    timeout_s: int = 120,
) -> dict[str, Any]:
    """Call DeepSeek chat completions. On success returns a sanitized record.

    Never includes headers or the API key in the return value.
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not set in the environment")

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
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
    # Drop the key from this scope after the request object is built.
    del api_key

    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as resp:
            status = getattr(resp, "status", 200)
            raw = resp.read()
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": _error_payload(exc),
            "request_payload": {
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "url": DEEPSEEK_URL,
                # Exact messages are stored by the runner from its own copy,
                # not from this function's headers.
            },
        }
    finally:
        # Prevent accidental header reuse.
        request.headers = {}
        if hasattr(request, "unredirected_hdrs"):
            request.unredirected_hdrs = {}

    text = raw.decode("utf-8", errors="replace")
    text = redact(text)
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

    # Redact recursively just in case.
    body = json.loads(redact(json.dumps(body, ensure_ascii=False)))
    choice = {}
    if isinstance(body, dict) and body.get("choices"):
        choice = body["choices"][0] or {}
    message = (choice.get("message") or {}) if isinstance(choice, dict) else {}
    content = message.get("content") if isinstance(message, dict) else None
    usage = body.get("usage") if isinstance(body, dict) else None
    return {
        "ok": True,
        "http_status": status,
        "model": body.get("model") if isinstance(body, dict) else model,
        "id": body.get("id") if isinstance(body, dict) else None,
        "content": content,
        "finish_reason": choice.get("finish_reason") if isinstance(choice, dict) else None,
        "usage": usage,
        "raw_response": body,
    }
