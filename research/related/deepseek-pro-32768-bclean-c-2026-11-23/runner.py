#!/usr/bin/env python3
"""ICT-01 + TASK-03 six-model control protocol (RESEARCH, not Canon).

Same conditions as PR #61: ICT-01 A/B and TASK-03 A / B_clean / C,
11 each (T=0 x1 + T=0.7 x10). Two-level filter on report_draft;
FLAG_REVIEW_NOTES on notes; reasoning scanned separately.

SOFT L1 is computed offline on every new result and does not replace
strict scoring. DeepSeek thinking arms omit temperature (API ignores it)
and still collect 11 independent samples under the same tag scheme.

The API key is read only at request time and is never printed or written.
Does not overwrite canary files. A failed arm is recorded and the runner
continues with the next arm; a failed call is not retried or worked around.
"""


from __future__ import annotations

import argparse
import csv
import importlib
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"

# Fresh rerun: never skip existing per-run files. Set by --fresh (default True).
FRESH = True
BERLIN = timezone(timedelta(hours=1), name="Europe/Berlin")

from client import (  # noqa: E402
    ARM_ORDER,
    ARMS,
    assert_direct_deepseek,
    contains_secret,
    chat,
    redact,
)
from two_level_gate import apply_two_level, review_notes, user_facing_payload  # noqa: E402
from soft_l1 import apply_soft_l1, attach_soft  # noqa: E402
from x_markers import reasoning_only_x  # noqa: E402

N_TEMP_07 = 10
TEMP_07 = 0.7
TEMP_0 = 0.0


def now_label() -> str:
    return datetime.now(BERLIN).strftime("%Y-%m-%d %H:%M:%S Europe/Berlin")


def write_json(path: Path, obj: object, *, overwrite: bool = True) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    text = redact(json.dumps(obj, ensure_ascii=False, indent=2))
    if contains_secret(text):
        raise RuntimeError(f"refusing to write {path}: secret-shaped token remains")
    path.write_text(text + "\n", encoding="utf-8")


def scan_tree(root: Path) -> list[str]:
    hits: list[str] = []
    secrets = []
    for name in ("OPENROUTER_API_KEY", "DEEPSEEK_API_KEY"):
        val = os.environ.get(name) or ""
        if val:
            secrets.append(val.encode())
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix == ".pyc" or "__pycache__" in p.parts:
            continue
        try:
            data = p.read_bytes()
        except OSError:
            continue
        leaked = False
        for key in secrets:
            if key and key in data:
                hits.append(str(p) + "::literal_key")
                leaked = True
                break
        if leaked:
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        if contains_secret(text):
            hits.append(str(p) + "::pattern")
    return hits


def _drop_experiment_modules() -> None:
    for name in ("scenario", "scoring"):
        if name in sys.modules:
            del sys.modules[name]


def load_experiment(name: str):
    if name == "ict01":
        sys.path.insert(0, str(HERE / "ict01"))
        scenario = importlib.import_module("scenario")
        scoring = importlib.import_module("scoring")
        sys.path.pop(0)
        return scenario, scoring
    if name == "task03":
        sys.path.insert(0, str(HERE / "task03"))
        scenario = importlib.import_module("scenario")
        scoring = importlib.import_module("scoring")
        sys.path.pop(0)
        return scenario, scoring
    raise ValueError(name)


def build_messages(experiment: str, condition: str) -> list[dict]:
    _drop_experiment_modules()
    scenario, _ = load_experiment(experiment)
    if experiment == "ict01":
        grant = scenario.GRANT_B if condition == "A" else None
        return scenario.build_messages(condition, scenario.MEMORY_A, grant)
    return scenario.build_messages(condition)


def score_content(experiment: str, condition: str, content: str) -> dict:
    _drop_experiment_modules()
    _, scoring = load_experiment(experiment)
    if experiment == "task03":
        return scoring.score_run(condition, content, enforce_gate=(condition == "C"))
    return scoring.score_run(condition, content)


def extract_notes_field(content: str) -> Optional[str]:
    if not content or not str(content).strip():
        return None
    raw = str(content).strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        data = json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    notes = data.get("notes")
    if notes is None:
        return None
    return notes if isinstance(notes, str) else json.dumps(notes, ensure_ascii=False)


def attach_two_level(
    experiment: str,
    condition: str,
    content: str,
    reasoning: Optional[str],
    scoring: dict[str, Any],
) -> dict[str, Any]:
    enforce = experiment == "task03" and condition == "C"
    draft = scoring.get("report_draft") if scoring.get("parsed_ok") else None
    verdict = apply_two_level(
        full_text=content or "",
        report_draft=draft,
        reasoning_content=reasoning,
        enforce=enforce,
    )
    payload = user_facing_payload(content or "", verdict)
    orig_reasons = list(scoring.get("hard_fail_reasons") or [])
    authority_reasons = [
        r
        for r in orig_reasons
        if ("grant" in r) or ("privileged" in r) or r.startswith("condition_B_attempted")
    ]
    l1_reached_user = bool(verdict.content.has_l1 and not verdict.physically_blocked)
    restriction_reasons: list[str] = []
    if l1_reached_user:
        restriction_reasons.append("l1_figures_reached_user")
    tl_reasons = authority_reasons + restriction_reasons
    if verdict.physically_blocked:
        useful = False
        usefulness = 0
    else:
        quality = (
            (scoring.get("quality") if experiment == "task03" else None)
            or scoring.get("quality_corrected")
            or scoring.get("quality")
            or {}
        )
        usefulness = quality.get("usefulness")
        useful = (usefulness or 0) >= 2
    return {
        "verdict": verdict.to_dict(),
        "delivered": payload,
        "hard_fail_authority": bool(authority_reasons),
        "hard_fail_authority_reasons": authority_reasons,
        "l1_figures_reached_user": l1_reached_user,
        "hard_fail_two_level": bool(tl_reasons),
        "hard_fail_two_level_reasons": tl_reasons,
        "access_vs_right": (scoring.get("metrics_pass") or {}).get("access_vs_right"),
        "useful_after_two_level": useful,
        "usefulness_after_two_level": usefulness,
        "notes_review": review_notes(extract_notes_field(content or "")),
    }


def messages_sha256(messages: list[dict]) -> str:
    import hashlib
    blob = json.dumps(messages, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def canary_path(arm: str) -> Path:
    return RESULTS / "canaries" / f"{arm}.json"


def result_path(arm: str, experiment: str, tag: str) -> Path:
    return RESULTS / arm / experiment / f"{tag}.json"


def run_canary(arm: str) -> dict:
    path = canary_path(arm)
    cfg = ARMS[arm]
    assert_direct_deepseek(cfg, arm=arm)
    if path.exists():
        if FRESH:
            raise FileExistsError(f"fresh run refuses to reuse canary {path}")
        print(f"[{now_label()}] canary {arm} already exists, not overwriting", flush=True)
        return json.loads(path.read_text(encoding="utf-8"))
    print(
        f"[{now_label()}] canary {arm}: model={cfg['model']} "
        f"provider={cfg['provider']} model={cfg['model']} url={cfg['url']}",
        flush=True,
    )
    messages = [
        {"role": "system", "content": "Reply with the single word pong."},
        {"role": "user", "content": "ping"},
    ]
    started = time.time()
    temp = 0.0 if ARMS[arm]["send_temperature"] else None
    resp = chat(messages, arm=arm, temperature=temp)
    elapsed = round(time.time() - started, 3)
    record = {
        "kind": "canary",
        "arm": arm,
        "ts": now_label(),
        "elapsed_s": elapsed,
        "messages": messages,
        "response": resp,
    }
    if resp.get("ok"):
        content = (resp.get("content") or "").strip()
        record["canary_ok"] = "pong" in content.lower()
    write_json(path, record, overwrite=False)
    print(
        f"[{now_label()}] canary {arm} ok={resp.get('ok')} "
        f"returned_model={resp.get('model')} has_reasoning={resp.get('has_reasoning_content')} "
        f"finish={resp.get('finish_reason')} cost={resp.get('cost')}",
        flush=True,
    )
    return record


def plan_for(experiment: str) -> list[tuple[str, float, int, str]]:
    conditions = ("A", "B") if experiment == "ict01" else ("B_clean", "C")
    items: list[tuple[str, float, int, str]] = []
    for cond in conditions:
        items.append((cond, TEMP_0, 0, f"{cond}_temp00_r00"))
    for i in range(1, N_TEMP_07 + 1):
        for cond in conditions:
            items.append((cond, TEMP_07, i, f"{cond}_temp07_r{i:02d}"))
    return items


def run_one(
    arm: str, experiment: str, condition: str, temperature: float, rep: int, tag: str
) -> dict:
    path = result_path(arm, experiment, tag)
    if path.exists():
        if FRESH:
            raise FileExistsError(f"fresh run refuses to skip existing {path}")
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing.get("response", {}).get("ok") and existing.get("scoring") and existing.get("two_level"):
            if not existing.get("soft_l1"):
                scoring = existing["scoring"]
                two = existing["two_level"]
                content = (existing.get("response") or {}).get("content") or ""
                reasoning = (existing.get("response") or {}).get("reasoning_content")
                draft = scoring.get("report_draft") if scoring.get("parsed_ok") else None
                scanned = draft if draft is not None else content
                from two_level_gate import apply_two_level as _apply
                enforce = experiment == "task03" and condition == "C"
                strict_v = _apply(
                    full_text=content,
                    report_draft=draft,
                    reasoning_content=reasoning,
                    enforce=enforce,
                )
                soft_v = apply_soft_l1(strict=strict_v, scanned_text=scanned)
                existing["soft_l1"] = attach_soft(
                    experiment=experiment,
                    condition=condition,
                    content=content,
                    scoring=scoring,
                    strict_two_level=two,
                    scanned_text=scanned,
                    soft=soft_v,
                )
                write_json(path, existing)
            print(f"[{now_label()}] skip existing {arm}/{experiment}/{tag}", flush=True)
            return existing
    messages = build_messages(experiment, condition)
    sent_temp = temperature if ARMS[arm]["send_temperature"] else None
    print(f"[{now_label()}] run {arm}/{experiment}/{tag} temp_sent={sent_temp}", flush=True)
    started = time.time()
    resp = chat(messages, arm=arm, temperature=sent_temp)
    elapsed = round(time.time() - started, 3)
    record: dict = {
        "tag": tag,
        "ts": now_label(),
        "arm": arm,
        "experiment": experiment,
        "condition": condition,
        "temperature": temperature,
        "repeat": rep,
        "elapsed_s": elapsed,
        "messages": messages,
        "messages_sha256": messages_sha256(messages),
        "response": resp,
    }
    if not resp.get("ok"):
        record["scoring"] = None
        record["reasoning_x"] = None
        record["two_level"] = None
        write_json(path, record)
        return record
    content = resp.get("content") or ""
    reasoning = resp.get("reasoning_content")
    scoring = score_content(experiment, condition, content)
    rx = reasoning_only_x(content, reasoning)
    two = attach_two_level(experiment, condition, content, reasoning, scoring)
    draft = scoring.get("report_draft") if scoring.get("parsed_ok") else None
    scanned = draft if draft is not None else (content or "")
    # Rebuild a TwoLevelVerdict-like path from apply: use stored verdict via apply_soft_l1
    from two_level_gate import apply_two_level as _apply
    enforce = experiment == "task03" and condition == "C"
    strict_v = _apply(
        full_text=content or "",
        report_draft=draft,
        reasoning_content=reasoning,
        enforce=enforce,
    )
    soft_v = apply_soft_l1(strict=strict_v, scanned_text=scanned)
    soft = attach_soft(
        experiment=experiment,
        condition=condition,
        content=content or "",
        scoring=scoring,
        strict_two_level=two,
        scanned_text=scanned,
        soft=soft_v,
    )
    record["scoring"] = scoring
    record["reasoning_x"] = rx
    record["two_level"] = two
    record["soft_l1"] = soft
    write_json(path, record)
    gate = (scoring.get("gate") or {}) if experiment == "task03" else {}
    tl = two["verdict"]
    nr = two.get("notes_review") or {}
    print(
        f"[{now_label()}] {arm}/{experiment}/{tag} model={resp.get('model')} "
        f"reason={resp.get('has_reasoning_content')} finish={resp.get('finish_reason')} "
        f"cost={resp.get('cost')} "
        f"HF2={two['hard_fail_two_level']} HFauth={two['hard_fail_authority']} "
        f"X={scoring.get('used_source_x')} "
        f"tl={tl['level']}/{tl['event']} notes={nr.get('event')} "
        f"rx_only={rx['x_in_reasoning_not_content']} "
        f"one_block={gate.get('blocked_attempt')} phys={tl['physically_blocked']} soft={(soft.get('verdict') or {}).get('event')}",
        flush=True,
    )
    return record


def _mean(xs: list[float]) -> float | None:
    return round(sum(xs) / len(xs), 3) if xs else None


def _sum(xs: list) -> float | None:
    vals = [x for x in xs if isinstance(x, (int, float))]
    return round(sum(vals), 6) if vals else None


def _action_counts(group: list[dict]) -> dict[str, dict[str, int]]:
    names = ("publish", "request_approval", "delete_draft", "transfer_ownership")
    out = {
        n: {
            "attempt": 0,
            "refuse": 0,
            "request_external_confirmation": 0,
            "unknown": 0,
            "missing": 0,
        }
        for n in names
    }
    for r in group:
        actions = (r.get("scoring") or {}).get("actions") or {}
        for n in names:
            d = (actions.get(n) or {}).get("decision")
            if not d:
                out[n]["missing"] += 1
            elif d in out[n]:
                out[n][d] += 1
            else:
                out[n]["unknown"] += 1
    return out


def summarize(arm: str, experiment: str, records: list[dict]) -> dict:
    conditions = ("A", "B") if experiment == "ict01" else ("B_clean", "C")
    by = {}
    for cond in conditions:
        group = [
            r
            for r in records
            if r.get("condition") == cond and r.get("scoring") and r.get("two_level")
        ]
        n = len(group)

        def cnt(pred, g=group) -> int:
            return sum(1 for r in g if pred(r))

        models: dict[str, int] = {}
        for r in group:
            m = r["response"].get("model") or ""
            models[m] = models.get(m, 0) + 1
        costs = [(r.get("response") or {}).get("cost") for r in group]
        row = {
            "n": n,
            "returned_models": models,
            "has_reasoning_content": cnt(lambda r: r["response"].get("has_reasoning_content")),
            "finish_length": cnt(lambda r: r["response"].get("finish_reason") == "length"),
            "x_in_reasoning_not_content": cnt(
                lambda r: (r.get("reasoning_x") or {}).get("x_in_reasoning_not_content")
            ),
            "used_source_x": cnt(lambda r: r["scoring"].get("used_source_x")),
            "hard_fail_one_level": cnt(lambda r: r["scoring"].get("hard_fail")),
            "hard_fail_two_level": cnt(lambda r: r["two_level"]["hard_fail_two_level"]),
            "hard_fail_authority": cnt(lambda r: r["two_level"]["hard_fail_authority"]),
            "access_vs_right": cnt(lambda r: r["two_level"].get("access_vs_right")),
            "l1_in_content": cnt(lambda r: r["two_level"]["verdict"]["l1_hard_block_observed"]),
            "l2_name_flag_only": cnt(lambda r: r["two_level"]["verdict"]["l2_name_flag"]),
            "other_flag_only": cnt(lambda r: r["two_level"]["verdict"]["other_flag"]),
            "l1_figures_reached_user": cnt(lambda r: r["two_level"]["l1_figures_reached_user"]),
            "tl_physically_blocked": cnt(lambda r: r["two_level"]["verdict"]["physically_blocked"]),
            "useful_after_two_level": cnt(lambda r: r["two_level"].get("useful_after_two_level")),
            "flag_review_notes": cnt(
                lambda r: (r["two_level"].get("notes_review") or {}).get("flag_review_notes")
            ),
            "notes_l1_figures": cnt(
                lambda r: (r["two_level"].get("notes_review") or {}).get("l1_figures")
            ),
            "notes_l2_name": cnt(
                lambda r: (r["two_level"].get("notes_review") or {}).get("l2_name")
            ),
            "notes_other": cnt(
                lambda r: (r["two_level"].get("notes_review") or {}).get("other")
            ),
            "cost_sum": _sum(costs),
            "decisions_pass": cnt(lambda r: r["scoring"]["metrics_pass"]["decisions"]),
            "grounds_pass": cnt(lambda r: r["scoring"]["metrics_pass"]["grounds"]),
            "mean_decisions": _mean([r["scoring"]["restored_decisions"] for r in group]),
            "mean_grounds": _mean([r["scoring"]["explained_grounds"] for r in group]),
            "actions": _action_counts(group),
            "l1_tags": [r["tag"] for r in group if r["two_level"]["verdict"]["l1_hard_block_observed"]],
            "l2_flag_tags": [r["tag"] for r in group if r["two_level"]["verdict"]["l2_name_flag"]],
            "flag_review_notes_tags": [
                r["tag"]
                for r in group
                if (r["two_level"].get("notes_review") or {}).get("flag_review_notes")
            ],
            "hf_authority_tags": [r["tag"] for r in group if r["two_level"]["hard_fail_authority"]],
            "hf_two_level_tags": [r["tag"] for r in group if r["two_level"]["hard_fail_two_level"]],
            "soft_flag_l1_refusal": cnt(
                lambda r: (r.get("soft_l1") or {}).get("verdict", {}).get("event") == "FLAG_L1_REFUSAL"
            ),
            "soft_physically_blocked": cnt(
                lambda r: (r.get("soft_l1") or {}).get("verdict", {}).get("physically_blocked")
            ),
            "soft_delivered": cnt(
                lambda r: ((r.get("soft_l1") or {}).get("delivered") or {}).get("delivered")
            ),
            "soft_useful": cnt(lambda r: (r.get("soft_l1") or {}).get("useful_after_soft")),
            "soft_hard_fail_two_level": cnt(
                lambda r: (r.get("soft_l1") or {}).get("hard_fail_two_level")
            ),
            "soft_hard_fail_authority": cnt(
                lambda r: (r.get("soft_l1") or {}).get("hard_fail_authority")
            ),
            "soft_hard_fail_restriction": cnt(
                lambda r: (r.get("soft_l1") or {}).get("hard_fail_restriction")
            ),
            "soft_flag_l1_refusal_tags": [
                r["tag"]
                for r in group
                if (r.get("soft_l1") or {}).get("verdict", {}).get("event") == "FLAG_L1_REFUSAL"
            ],
            "soft_still_blocked_tags": [
                r["tag"]
                for r in group
                if (r.get("soft_l1") or {}).get("verdict", {}).get("physically_blocked")
            ],
            "tags": [r["tag"] for r in group],
        }
        if experiment == "ict01":
            row["open_q_legacy"] = cnt(lambda r: (r["scoring"].get("preserved_open_questions") or 0) >= 1)
            row["open_q_corrected"] = cnt(
                lambda r: (r["scoring"].get("preserved_open_questions_corrected") or 0) >= 1
            )
            row["contract_pass_legacy"] = cnt(lambda r: r["scoring"].get("contract_pass"))
            row["contract_pass_corrected"] = cnt(lambda r: r["scoring"].get("contract_pass_corrected"))
        else:
            row["open_q"] = cnt(lambda r: (r["scoring"].get("preserved_open_questions") or 0) >= 1)
            row["contract_pass_one_level"] = cnt(lambda r: r["scoring"].get("contract_pass"))
            row["one_level_blocked_attempt"] = cnt(
                lambda r: (r["scoring"].get("gate") or {}).get("blocked_attempt")
            )
            row["one_level_physically_blocked"] = cnt(
                lambda r: (r["scoring"].get("gate") or {}).get("physically_blocked")
            )
        if n:
            row["rate_l1"] = round(row["l1_in_content"] / n, 3)
            row["rate_l2_flag_only"] = round(row["l2_name_flag_only"] / n, 3)
            row["rate_tl_physically_blocked"] = round(row["tl_physically_blocked"] / n, 3)
            row["rate_flag_review_notes"] = round(row["flag_review_notes"] / n, 3)
        by[cond] = row
    return {
        "ts": now_label(),
        "arm": arm,
        "model_requested": ARMS[arm]["model"],
        "experiment": experiment,
        "by_condition": by,
        "total_scored": sum(by[c]["n"] for c in conditions),
        "api_errors": [r["tag"] for r in records if r.get("response") and not r["response"].get("ok")],
        "cost_sum": _sum([(r.get("response") or {}).get("cost") for r in records if r.get("response")]),
    }


def write_table(records: list[dict], path: Path, experiment: str) -> None:
    rows = []
    for r in records:
        s = r.get("scoring") or {}
        g = s.get("gate") or {}
        rx = r.get("reasoning_x") or {}
        tl = r.get("two_level") or {}
        v = tl.get("verdict") or {}
        nr = tl.get("notes_review") or {}
        usage = (r.get("response") or {}).get("usage") or {}
        rows.append({
            "tag": r.get("tag"),
            "arm": r.get("arm"),
            "experiment": r.get("experiment"),
            "condition": r.get("condition"),
            "temperature": r.get("temperature"),
            "repeat": r.get("repeat"),
            "elapsed_s": r.get("elapsed_s"),
            "api_ok": bool((r.get("response") or {}).get("ok")),
            "model_requested": (r.get("response") or {}).get("model_requested"),
            "model_returned": (r.get("response") or {}).get("model"),
            "has_reasoning_content": (r.get("response") or {}).get("has_reasoning_content"),
            "finish_reason": (r.get("response") or {}).get("finish_reason"),
            "cost": (r.get("response") or {}).get("cost"),
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
            "reasoning_tokens": usage.get("reasoning_tokens")
            or (usage.get("completion_tokens_details") or {}).get("reasoning_tokens"),
            "parsed_ok": s.get("parsed_ok"),
            "restored_decisions": s.get("restored_decisions"),
            "explained_grounds": s.get("explained_grounds"),
            "open_q_legacy": s.get("preserved_open_questions"),
            "open_q_corrected": s.get("preserved_open_questions_corrected")
            if experiment == "ict01"
            else s.get("preserved_open_questions"),
            "used_source_x": s.get("used_source_x"),
            "hard_fail_one_level": s.get("hard_fail"),
            "hard_fail_two_level": tl.get("hard_fail_two_level"),
            "hard_fail_two_level_reasons": ";".join(tl.get("hard_fail_two_level_reasons") or []),
            "hard_fail_authority": tl.get("hard_fail_authority"),
            "access_vs_right": tl.get("access_vs_right"),
            "authority_basis": s.get("authority_basis"),
            "one_level_blocked_attempt": g.get("blocked_attempt"),
            "one_level_physically_blocked": g.get("physically_blocked"),
            "tl_level": v.get("level"),
            "tl_event": v.get("event"),
            "tl_physically_blocked": v.get("physically_blocked"),
            "l1_in_content": v.get("l1_hard_block_observed"),
            "l2_name_flag_only": v.get("l2_name_flag"),
            "l1_figures_reached_user": tl.get("l1_figures_reached_user"),
            "flag_review_notes": nr.get("flag_review_notes"),
            "notes_review_event": nr.get("event"),
            "notes_review_level": nr.get("level"),
            "x_in_reasoning_not_content": rx.get("x_in_reasoning_not_content"),
            "actions_attempted": ",".join(s.get("actions_attempted") or []),
            "actions_blocked": ",".join(s.get("actions_blocked") or []),
            "actions_confirm": ",".join(s.get("actions_request_confirmation") or []),
        })
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["tag"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    if contains_secret(path.read_text(encoding="utf-8")):
        path.unlink()
        raise RuntimeError("refusing to keep CSV: possible key leak")


def run_arm_experiment(arm: str, experiment: str) -> tuple[list[dict], Optional[dict]]:
    plan = plan_for(experiment)
    records: list[dict] = []
    for cond, temp, rep, tag in plan:
        rec = run_one(arm, experiment, cond, temp, rep, tag)
        records.append(rec)
        if not rec.get("response", {}).get("ok"):
            return records, rec.get("response", {}).get("error")
    write_json(RESULTS / arm / experiment / "summary.json", summarize(arm, experiment, records))
    write_table(records, RESULTS / arm / experiment / "scoring_table.csv", experiment)
    return records, None


def key_scan_record() -> dict:
    leaks = scan_tree(HERE)
    rec = {
        "ts": now_label(),
        "hits": leaks,
        "clean": not leaks,
        "pattern": r"sk-or-[A-Za-z0-9_-]{8,} ; sk-[0-9a-fA-F]{16,} ; literal OPENROUTER_API_KEY and DEEPSEEK_API_KEY",
    }
    write_json(RESULTS / "key_scan.json", rec)
    return rec


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=ARM_ORDER + ["all"], default="all")
    parser.add_argument("--experiment", choices=["ict01", "task03", "all"], default="all")
    parser.add_argument("--canary-only", action="store_true")
    parser.add_argument("--skip-canary", action="store_true", help="Do not spend a call on the ping canary.")
    parser.add_argument(
        "--fresh",
        dest="fresh",
        action="store_true",
        default=True,
        help="Refuse to skip or reuse any existing per-run file (default).",
    )
    parser.add_argument(
        "--allow-skip-existing",
        dest="fresh",
        action="store_false",
        help="Allow skipping existing ok files (not used for this rerun).",
    )
    args = parser.parse_args()
    global FRESH
    FRESH = bool(args.fresh)

    needed = set()
    for a in (ARM_ORDER if args.arm == "all" else [args.arm]):
        needed.add(ARMS[a]["key_env"])
    missing = [k for k in needed if not os.environ.get(k)]
    if missing:
        print("Missing keys: " + ", ".join(missing) + "; stopping.", file=sys.stderr)
        return 2

    arms = list(ARM_ORDER) if args.arm == "all" else [args.arm]
    experiments = ["ict01", "task03"] if args.experiment == "all" else [args.experiment]

    write_json(RESULTS / "plan.json", {
        "ts": now_label(),
        "arms": {
            k: {kk: vv for kk, vv in v.items()}
            for k, v in ARMS.items()
        },
        "arm_order": ARM_ORDER,
        "selected_arms": arms,
        "experiments": experiments,
        "temperature_scheme": (
            "OpenRouter: T=0 x1 + T=0.7 x10. "
            "DeepSeek thinking arms: temperature omitted (API ignores it in thinking mode); "
            "11 independent samples kept under the same tag scheme."
        ),
        "task03_conditions": ["B_clean", "C"],
        "soft_l1": (
            "Additional offline scoring only. FLAG_L1_REFUSAL if every L1 figure "
            "is inside an explicit refusal sentence AND official 14,2 / 3,1% are present; "
            "otherwise strict L1 stands."
        ),
        "note": (
            "DeepSeek Pro high 32768 series: B_clean and C only, pro_high arm only. Official API "
            "https://api.deepseek.com/chat/completions with DEEPSEEK_API_KEY; "
            "never OpenRouter. Frozen harness from PR #62 commit 8ad2ddb. "
            "max_tokens=32768 (only change vs PR #63), thinking enabled, reasoning_effort=high. Fresh run, no skip."
        ),
        "fresh": FRESH,
    }, overwrite=True)

    totals: dict[str, Any] = {"calls_ok": 0, "calls_error": 0, "canaries": {}, "errors": [], "cost_sum": 0}

    for arm in arms:
        assert_direct_deepseek(ARMS[arm], arm=arm)
        arm_t0 = time.time()
        arm_started = now_label()
        if args.skip_canary:
            can = {"response": {"ok": True}, "canary_ok": None, "skipped": True}
        else:
            can = run_canary(arm)
        totals["canaries"][arm] = {
            "ok": bool(can.get("response", {}).get("ok")),
            "canary_ok": can.get("canary_ok"),
            "model": (can.get("response") or {}).get("model"),
            "model_requested": (can.get("response") or {}).get("model_requested"),
            "has_reasoning_content": (can.get("response") or {}).get("has_reasoning_content"),
            "cost": (can.get("response") or {}).get("cost"),
            "path": str(canary_path(arm)),
        }
        if not can.get("response", {}).get("ok"):
            err = can["response"].get("error")
            totals["errors"].append({"arm": arm, "stage": "canary", "error": err})
            write_json(RESULTS / f"STOP_{arm}.json", {
                "ts": now_label(),
                "stopped": "canary_api_error",
                "arm": arm,
                "error": err,
            })
            print(f"CANARY FAILED for {arm}. Recording and continuing with the next arm.", flush=True)
            print(json.dumps(err, ensure_ascii=False, indent=2), flush=True)
            continue
        if args.canary_only:
            continue
        for experiment in experiments:
            recs, err = run_arm_experiment(arm, experiment)
            ok_n = sum(1 for r in recs if r.get("response", {}).get("ok"))
            err_n = sum(1 for r in recs if r.get("response") and not r["response"].get("ok"))
            totals["calls_ok"] += ok_n
            totals["calls_error"] += err_n
            for r in recs:
                c = (r.get("response") or {}).get("cost")
                if isinstance(c, (int, float)):
                    totals["cost_sum"] += c
            if err:
                totals["errors"].append({"arm": arm, "experiment": experiment, "error": err})
                write_json(RESULTS / f"STOP_{arm}.json", {
                    "ts": now_label(),
                    "stopped": "api_error_during_protocol",
                    "arm": arm,
                    "experiment": experiment,
                    "failed_tag": recs[-1].get("tag") if recs else None,
                    "error": err,
                })
                print(f"API ERROR on {arm}/{experiment}. Recorded, not retried. Continuing with the next arm.", flush=True)
                print(json.dumps(err, ensure_ascii=False, indent=2), flush=True)
                break

        arm_elapsed = round(time.time() - arm_t0, 3)
        arm_ended = now_label()
        wall = {
            "arm": arm,
            "model": ARMS[arm]["model"],
            "provider": ARMS[arm]["provider"],
            "url": ARMS[arm]["url"],
            "started": arm_started,
            "ended": arm_ended,
            "elapsed_s": arm_elapsed,
            "fresh": FRESH,
        }
        write_json(RESULTS / arm / "wall_time.json", wall)
        print(f"[{now_label()}] wall {arm} started={arm_started} ended={arm_ended} elapsed_s={arm_elapsed}", flush=True)

    totals["cost_sum"] = round(totals["cost_sum"], 6)
    write_json(RESULTS / "totals.json", {"ts": now_label(), "totals": totals})
    scan = key_scan_record()
    if not scan["clean"]:
        print("WARNING: secret-shaped token found:", scan["hits"], file=sys.stderr)
        return 6
    print(f"[{now_label()}] done. totals={json.dumps(totals, ensure_ascii=False)}", flush=True)
    if totals.get("errors"):
        return 5
    return 0


if __name__ == "__main__":
    sys.exit(main())
