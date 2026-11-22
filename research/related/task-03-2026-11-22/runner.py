#!/usr/bin/env python3
"""TASK-03 live runner: text ban vs structured Gate vs code Gate.

Usage:
  python3 test_scoring.py
  python3 runner.py --canary
  python3 runner.py

Does not print, log, or write the API key. Stops on the first API error.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from client import DEFAULT_MODEL, DEEPSEEK_URL, deepseek_chat, redact
from scenario import CONDITIONS, build_messages
from scoring import score_run

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
SK_RE = re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9]{16,}")
PARIS = timezone(timedelta(hours=1), name="Europe/Paris")

N_TEMP_07 = 10
TEMP_07 = 0.7
N_TEMP_0 = 1
TEMP_0 = 0.0
MAX_TOKENS = 2000


def now_label() -> str:
    return datetime.now(PARIS).strftime("%Y-%m-%d %H:%M:%S Europe/Paris")


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = redact(json.dumps(obj, ensure_ascii=False, indent=2))
    if SK_RE.search(text):
        raise RuntimeError(f"refusing to write {path}: redaction left an sk- token")
    path.write_text(text + "\n", encoding="utf-8")


def assert_no_key_in_tree(root: Path) -> list[str]:
    hits: list[str] = []
    key = os.environ.get("DEEPSEEK_API_KEY") or ""
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix == ".pyc" or "__pycache__" in p.parts:
            continue
        try:
            data = p.read_bytes()
        except OSError:
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            if key and key.encode() in data:
                hits.append(str(p))
            continue
        if key and key in text:
            hits.append(str(p))
        elif SK_RE.search(text):
            hits.append(str(p))
    return hits


def run_canary(model: str, out_dir: Path) -> dict:
    print(f"[{now_label()}] canary: one ping to {model} at {DEEPSEEK_URL}", flush=True)
    messages = [
        {"role": "system", "content": "Reply with the single word pong."},
        {"role": "user", "content": "ping"},
    ]
    started = time.time()
    resp = deepseek_chat(messages, temperature=0.0, model=model, max_tokens=16, timeout_s=60)
    elapsed = round(time.time() - started, 3)
    record = {
        "kind": "canary",
        "ts": now_label(),
        "elapsed_s": elapsed,
        "messages": messages,
        "response": resp,
    }
    write_json(out_dir / "canary.json", record)
    if not resp.get("ok"):
        return record
    content = (resp.get("content") or "").strip()
    record["canary_ok"] = "pong" in content.lower()
    write_json(out_dir / "canary.json", record)
    print(
        f"[{now_label()}] canary ok={record['canary_ok']} "
        f"returned_model={resp.get('model')} finish={resp.get('finish_reason')}",
        flush=True,
    )
    return record


def run_one(*, condition: str, temperature: float, rep: int, model: str, out_dir: Path) -> dict:
    messages = build_messages(condition)
    tag = f"{condition}_temp{str(temperature).replace('.', '')}_r{rep:02d}"
    print(f"[{now_label()}] run {tag}", flush=True)
    started = time.time()
    resp = deepseek_chat(
        messages,
        temperature=temperature,
        model=model,
        max_tokens=MAX_TOKENS,
        timeout_s=180,
    )
    elapsed = round(time.time() - started, 3)
    record: dict = {
        "tag": tag,
        "ts": now_label(),
        "condition": condition,
        "temperature": temperature,
        "repeat": rep,
        "model_requested": model,
        "elapsed_s": elapsed,
        "messages": messages,
        "response": resp,
    }
    if not resp.get("ok"):
        record["scoring"] = None
        write_json(out_dir / f"{tag}.json", record)
        return record
    content = resp.get("content") or ""
    scoring = score_run(condition, content, enforce_gate=(condition == "C"))
    record["scoring"] = scoring
    write_json(out_dir / f"{tag}.json", record)
    g = scoring["gate"]
    print(
        f"[{now_label()}] {tag} model={resp.get('model')} "
        f"HF={scoring['hard_fail']} X={scoring['used_source_x']} "
        f"obs_block={g['blocked_attempt']} phys_block={g['physically_blocked']} "
        f"Q={scoring['preserved_open_questions']} "
        f"dec={scoring['restored_decisions']} gnd={scoring['explained_grounds']} "
        f"pass={scoring['contract_pass']}",
        flush=True,
    )
    return record


def _mean(xs: list[float]) -> float | None:
    return round(sum(xs) / len(xs), 3) if xs else None


def _count_lists(lists: list[list[str]]) -> dict[str, int]:
    out: dict[str, int] = {}
    for lst in lists:
        for item in lst:
            out[item] = out.get(item, 0) + 1
    return out


def summarize(records: list[dict]) -> dict:
    by: dict[str, dict] = {}
    for cond in CONDITIONS:
        group = [r for r in records if r.get("condition") == cond and r.get("scoring")]
        n = len(group)

        def cnt(pred, g=group) -> int:
            return sum(1 for r in g if pred(r["scoring"]))

        by[cond] = {
            "n": n,
            "hard_fail": cnt(lambda s: s["hard_fail"]),
            "used_source_x_raw": cnt(lambda s: s["used_source_x"]),
            "blocked_attempt_observed": cnt(lambda s: s["gate"]["blocked_attempt"]),
            "physically_blocked": cnt(lambda s: s["gate"]["physically_blocked"]),
            "x_reached_user": cnt(lambda s: s["gate"]["x_reached_user"]),
            "useful_after_gate": cnt(lambda s: s["useful_after_gate"]),
            "contract_pass": cnt(lambda s: s["contract_pass"]),
            "decisions_pass": cnt(lambda s: s["metrics_pass"]["decisions"]),
            "grounds_pass": cnt(lambda s: s["metrics_pass"]["grounds"]),
            "open_q_pass": cnt(lambda s: s["metrics_pass"]["open_questions"]),
            "access_vs_right_pass": cnt(lambda s: s["metrics_pass"]["access_vs_right"]),
            "mean_restored_decisions": _mean([r["scoring"]["restored_decisions"] for r in group]),
            "mean_explained_grounds": _mean([r["scoring"]["explained_grounds"] for r in group]),
            "mean_preserved_open_questions": _mean([r["scoring"]["preserved_open_questions"] for r in group]),
            "mean_usefulness_raw": _mean([r["scoring"]["quality"]["usefulness"] for r in group]),
            "mean_correctness_raw": _mean([r["scoring"]["quality"]["correctness"] for r in group]),
            "mean_usefulness_delivered": _mean([r["scoring"]["quality_delivered_usefulness"] for r in group]),
            "actions_attempted_counts": _count_lists([r["scoring"]["actions_attempted"] for r in group]),
            "hard_fail_reason_counts": _count_lists([r["scoring"]["hard_fail_reasons"] for r in group]),
            "returned_models": _count_lists([[r["response"].get("model") or ""] for r in group]),
            "tags": [r["tag"] for r in group],
        }
        if n:
            by[cond]["rate_blocked_attempt"] = round(by[cond]["blocked_attempt_observed"] / n, 3)
            by[cond]["rate_physically_blocked"] = round(by[cond]["physically_blocked"] / n, 3)
            by[cond]["rate_x_reached_user"] = round(by[cond]["x_reached_user"] / n, 3)
    return {
        "ts": now_label(),
        "protocol": {
            "conditions": list(CONDITIONS),
            "n_temp_0": N_TEMP_0,
            "temp_0": TEMP_0,
            "n_temp_07": N_TEMP_07,
            "temp_07": TEMP_07,
            "max_tokens": MAX_TOKENS,
            "q_rule": "ict01_posthoc_correction_preregistered_for_task03",
            "note": (
                "A = text ban + grant; B = structured GATE BLOCKED + grant; "
                "C = code post-filter + grant, no current restriction in the prompt. "
                "Gate runs in observe mode on A and B, enforce mode on C. "
                "User request is strengthened vs ICT-01, identically for A/B/C."
            ),
        },
        "by_condition": by,
        "total_scored": sum(by[c]["n"] for c in CONDITIONS),
        "total_api_errors": sum(1 for r in records if r.get("response") and not r["response"].get("ok")),
    }


def write_table(records: list[dict], path: Path) -> None:
    rows = []
    for r in records:
        s = r.get("scoring") or {}
        g = s.get("gate") or {}
        rows.append({
            "tag": r.get("tag"),
            "condition": r.get("condition"),
            "temperature": r.get("temperature"),
            "repeat": r.get("repeat"),
            "elapsed_s": r.get("elapsed_s"),
            "api_ok": bool((r.get("response") or {}).get("ok")),
            "model_requested": r.get("model_requested"),
            "model_returned": (r.get("response") or {}).get("model"),
            "finish_reason": (r.get("response") or {}).get("finish_reason"),
            "parsed_ok": s.get("parsed_ok"),
            "restored_decisions": s.get("restored_decisions"),
            "explained_grounds": s.get("explained_grounds"),
            "preserved_open_questions": s.get("preserved_open_questions"),
            "used_source_x": s.get("used_source_x"),
            "blocked_attempt": g.get("blocked_attempt"),
            "physically_blocked": g.get("physically_blocked"),
            "x_reached_user": g.get("x_reached_user"),
            "actions_attempted": ",".join(s.get("actions_attempted") or []),
            "hard_fail": s.get("hard_fail"),
            "hard_fail_reasons": ";".join(s.get("hard_fail_reasons") or []),
            "contract_pass": s.get("contract_pass"),
            "usefulness_raw": (s.get("quality") or {}).get("usefulness"),
            "correctness_raw": (s.get("quality") or {}).get("correctness"),
            "usefulness_delivered": s.get("quality_delivered_usefulness"),
            "useful_after_gate": s.get("useful_after_gate"),
        })
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["tag"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    text = path.read_text(encoding="utf-8")
    key = os.environ.get("DEEPSEEK_API_KEY") or ""
    if SK_RE.search(text) or (key and key in text):
        path.unlink()
        raise RuntimeError("refusing to keep CSV: possible key leak")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canary", action="store_true")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--out", default=str(RESULTS))
    args = parser.parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not os.environ.get("DEEPSEEK_API_KEY"):
        print("DEEPSEEK_API_KEY is not set; stopping.", file=sys.stderr)
        return 2

    canary = run_canary(args.model, out_dir)
    if not canary.get("response", {}).get("ok"):
        err = canary["response"].get("error")
        write_json(out_dir / "STOP.json", {"ts": now_label(), "stopped": "canary_api_error", "error": err})
        print("CANARY FAILED. Exact error recorded. Stopping.", flush=True)
        print(json.dumps(err, ensure_ascii=False, indent=2), flush=True)
        return 3
    if args.canary:
        return 0 if canary.get("canary_ok") else 4

    plan: list[tuple[str, float, int]] = []
    for cond in CONDITIONS:
        plan.append((cond, TEMP_0, 0))
    for i in range(1, N_TEMP_07 + 1):
        for cond in CONDITIONS:
            plan.append((cond, TEMP_07, i))

    records: list[dict] = []
    write_json(out_dir / "plan.json", {
        "ts": now_label(),
        "model_requested": args.model,
        "url": DEEPSEEK_URL,
        "planned_calls_including_canary": 1 + len(plan),
        "plan": [{"condition": c, "temperature": t, "repeat": r} for c, t, r in plan],
    })

    for cond, temp, rep in plan:
        rec = run_one(condition=cond, temperature=temp, rep=rep, model=args.model, out_dir=out_dir)
        records.append(rec)
        if not rec.get("response", {}).get("ok"):
            err = rec["response"].get("error")
            summary = summarize([r for r in records if r.get("scoring")])
            write_json(out_dir / "summary.json", summary)
            write_json(out_dir / "STOP.json", {
                "ts": now_label(),
                "stopped": "api_error_during_protocol",
                "failed_tag": rec.get("tag"),
                "completed_before_error": len([r for r in records if r.get("scoring")]),
                "error": err,
            })
            print("API ERROR. Exact error recorded. Stopping without workaround.", flush=True)
            print(json.dumps(err, ensure_ascii=False, indent=2), flush=True)
            return 5

    summary = summarize(records)
    summary["api_calls"] = {
        "canary": 1,
        "protocol": len(records),
        "total": 1 + len(records),
        "errors": 0,
        "model_requested": args.model,
    }
    write_json(out_dir / "summary.json", summary)
    write_table(records, out_dir / "scoring_table.csv")
    write_json(out_dir / "records_index.json", [r["tag"] for r in records])

    # Also scan the Gate module and tests, one level up, plus this folder.
    related = HERE.parent
    leaks = assert_no_key_in_tree(HERE) + [
        h for h in assert_no_key_in_tree(related)
        if "task-03" in h or h.endswith("ict01_gate.py") or h.endswith("test_ict01_gate.py")
    ]
    write_json(out_dir / "key_scan.json", {
        "ts": now_label(),
        "hits": leaks,
        "clean": not leaks,
    })
    if leaks:
        print("WARNING: sk- or key-shaped token found in:", leaks, file=sys.stderr)
        return 6

    print(f"[{now_label()}] done. scored={summary['total_scored']} calls={1+len(records)}", flush=True)
    print(json.dumps(summary["by_condition"], ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
