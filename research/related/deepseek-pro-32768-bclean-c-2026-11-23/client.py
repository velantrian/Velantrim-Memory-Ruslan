#!/usr/bin/env python3
"""Chat client for the 2026-11-23 DeepSeek Pro high max_tokens=32768 series (B_clean and C only).

Copied from PR #63 (commit 26d4016); only max_tokens changed (16384 -> 32768).

Calls DeepSeek's official API only:
  POST https://api.deepseek.com/chat/completions
with DEEPSEEK_API_KEY, read only at request time.
NEVER calls OpenRouter. OpenRouter arms from PR #62 are not present.

Arms:
  pro_high    deepseek-v4-pro, thinking enabled, reasoning_effort=high
  flash_high  deepseek-flash,  thinking enabled, reasoning_effort=high

Temperature is omitted (thinking mode ignores it). 11 independent
samples are still collected under the same tag scheme. max_tokens=16384.

Frozen scenario/scoring/two_level_gate from PR #62 (commit 8ad2ddb).
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any, Optional

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

OR_KEY_RE = re.compile(r"sk-or-[A-Za-z0-9_-]{8,}")
HEX_KEY_RE = re.compile(r"(?<![A-Za-z0-9])sk-[0-9a-fA-F]{16,}")

ARMS: dict[str, dict[str, Any]] = {
    "pro_high": {
        "provider": "deepseek",
        "model": "deepseek-v4-pro",
        "thinking": {"type": "enabled"},
        "reasoning_effort": "high",
        "send_temperature": False,
        # Only request-level difference from PR #63 (commit 26d4016): 16384 -> 32768.
        "max_tokens": 32768,
        # Client-side socket timeout only (not sent to the API): longer ceiling.
        "timeout_s": 1200,
        "url": DEEPSEEK_URL,
        "key_env": "DEEPSEEK_API_KEY",
    },
}

ARM_ORDER = ["pro_high"]

FORBIDDEN_URL_MARKERS = ("openrouter.ai", "openrouter.com")


def assert_direct_deepseek(cfg: dict[str, Any], *, arm: str) -> None:
    """Refuse any path that is not the official DeepSeek API."""
    url = str(cfg.get("url") or "")
    provider = str(cfg.get("provider") or "")
    key_env = str(cfg.get("key_env") or "")
    if provider != "deepseek":
        raise RuntimeError(f"{arm}: provider must be deepseek, got {provider!r}")
    if url != DEEPSEEK_URL:
        raise RuntimeError(f"{arm}: url must be {DEEPSEEK_URL}, got {url!r}")
    if key_env != "DEEPSEEK_API_KEY":
        raise RuntimeError(f"{arm}: key_env must be DEEPSEEK_API_KEY, got {key_env!r}")
    lowered = url.lower()
    if any(m in lowered for m in FORBIDDEN_URL_MARKERS):
        raise RuntimeError(f"{arm}: OpenRouter URL is forbidden in this rerun")


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
    if cfg.get("thinking") is not None:
        payload["thinking"] = dict(cfg["thinking"])
    if cfg.get("reasoning_effort"):
        payload["reasoning_effort"] = cfg["reasoning_effort"]
    if cfg.get("reasoning") is not None:
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


def extract_content(message: dict) -> Optional[str]:
    if not isinstance(message, dict):
        return None
    content = message.get("content")
    if isinstance(content, list):
        chunks = []
        for part in content:
            if isinstance(part, str):
                chunks.append(part)
            elif isinstance(part, dict) and part.get("type") in (None, "text"):
                chunks.append(str(part.get("text") or part.get("content") or ""))
        return "".join(chunks)
    return content


def chat(
    messages: list[dict[str, str]],
    *,
    arm: str,
    temperature: Optional[float] = None,
) -> dict[str, Any]:
    if arm not in ARMS:
        raise ValueError(f"unknown arm: {arm}")
    cfg = ARMS[arm]
    assert_direct_deepseek(cfg, arm=arm)
    api_key = os.environ.get(cfg["key_env"])
    if not api_key:
        raise RuntimeError(f"{cfg['key_env']} is not set in the environment")
    payload = build_payload(messages, arm=arm, temperature=temperature)
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        cfg["url"],
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    del api_key

    meta = {
        "model": payload["model"],
        "provider": cfg["provider"],
        "thinking": payload.get("thinking"),
        "reasoning_effort": payload.get("reasoning_effort"),
        "reasoning": payload.get("reasoning"),
        "temperature_sent": "temperature" in payload,
        "temperature": payload.get("temperature"),
        "max_tokens": payload.get("max_tokens"),
        "url": cfg["url"],
        "arm": arm,
    }

    try:
        with urllib.request.urlopen(request, timeout=cfg["timeout_s"]) as resp:
            status = getattr(resp, "status", 200)
            raw = resp.read()
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": _error_payload(exc), "request_payload_meta": meta}
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
    if isinstance(body, dict) and body.get("error"):
        return {
            "ok": False,
            "http_status": status,
            "error": {
                "type": "ProviderError",
                "message": redact(json.dumps(body.get("error"), ensure_ascii=False)[:4000]),
            },
            "request_payload_meta": meta,
        }

    choice = {}
    if isinstance(body, dict) and body.get("choices"):
        choice = body["choices"][0] or {}
    message = (choice.get("message") or {}) if isinstance(choice, dict) else {}
    content = extract_content(message) if isinstance(message, dict) else None
    reasoning = extract_reasoning(message) if isinstance(message, dict) else None
    usage = _usage(body) if isinstance(body, dict) else {}
    cost = None
    if isinstance(usage, dict):
        cost = usage.get("cost")
        if cost is None and isinstance(usage.get("cost_details"), dict):
            cost = usage["cost_details"].get("upstream_inference_cost")
    return {
        "ok": True,
        "http_status": status,
        "arm": arm,
        "provider": cfg["provider"],
        "model_requested": payload["model"],
        "model": body.get("model") if isinstance(body, dict) else payload["model"],
        "id": body.get("id") if isinstance(body, dict) else None,
        "content": content,
        "reasoning_content": reasoning,
        "has_reasoning_content": bool(reasoning),
        "finish_reason": choice.get("finish_reason") if isinstance(choice, dict) else None,
        "native_finish_reason": choice.get("native_finish_reason") if isinstance(choice, dict) else None,
        "usage": usage,
        "cost": cost,
        "thinking_requested": payload.get("thinking"),
        "reasoning_effort_requested": payload.get("reasoning_effort"),
        "reasoning_requested": payload.get("reasoning"),
        "temperature_sent": payload.get("temperature") if "temperature" in payload else None,
        "temperature_omitted_reason": (
            None
            if cfg["send_temperature"]
            else "DeepSeek thinking mode ignores temperature; parameter omitted"
        ),
        "max_tokens": payload.get("max_tokens"),
        "raw_response": body,
    }
