#!/usr/bin/env python3
"""ICT-01 live runner: Condition A vs Condition B via DeepSeek.

Usage:
  python test_scoring.py          # offline scorer checks
  python runner.py --canary       # one tiny API ping, then stop if it fails
  python runner.py                # full protocol (canary + A/B repeats)

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
from datetime import datetime, timezone, timedelta
from pathlib import Path

from client import DEFAULT_MODEL, DEEPSEEK_URL, deepseek_chat, redact
from scenario import GRANT_B, MEMORY_A, build_messages
from scoring import score_run

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
SK_RE = re.compile(r"sk-[A-Za-z0-9_\-]+")
PARIS = timezone(timedelta(hours=1), name="Europe/Paris")

# Pre-registered protocol (fixed before the live run).
N_TEMP_07 = 10
TEMP_07 = 0.7
N_TEMP_0 = 1
TEMP_0 = 0.0
MAX_TOKENS = 2000
CONDITIONS = ("A", "B")


def now_label() -> str:
    return datetime.now(PARIS).strftime("%Y-%m-%d %H:%M:%S %Z (Europe/Paris)")


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, ensure_ascii=False, indent=2)
    text = redact(text)
    if SK_RE.search(text):
        raise RuntimeError(f"refusing to write {path}: redaction left an sk- token")
    path.write_text(text + "\n", encoding="utf-8")


def assert_no_key_in_tree(root: Path) -> list[str]:
    hits: list[str] = []
    key = os.environ.get("DEEPSEEK_API_KEY") or ""
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix in {".pyc"} or p.name == "__pycache__":
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
    print(f"[{now_label()}] canary ok={record['canary_ok']} finish={resp.get('finish_reason')}", flush=True)
    return record


def run_one(
    *,
    condition: str,
    temperature: float,
    rep: int,
    model: str,
    out_dir: Path,
) -> dict:
    grant = GRANT_B if condition == "A" else None
    messages = build_messages(condition, MEMORY_A, grant)
    agent_id = "B" if condition == "A" else "C"
    tag = f"{condition}_temp{str(temperature).replace('.', '')}_r{rep:02d}"
    print(f"[{now_label()}] run {tag} agent={agent_id}", flush=True)
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
        "agent_id": agent_id,
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
    scoring = score_run(condition, content)
    record["scoring"] = scoring
    write_json(out_dir / f"{tag}.json", record)
    hf = "HARD FAIL" if scoring["hard_fail"] else "ok"
    print(
        f"[{now_label()}] {tag} {hf} decisions={scoring['restored_decisions']} "
        f"grounds={scoring['explained_grounds']} Q={scoring['preserved_open_questions']} "
        f"X={scoring['used_source_x']} attempted={scoring['actions_attempted']} "
        f"pass={scoring['contract_pass']}",
        flush=True,
    )
    return record


def summarize(records: list[dict]) -> dict:
    by: dict[str, dict] = {}
    for cond in CONDITIONS:
        group = [r for r in records if r.get("condition") == cond and r.get("scoring")]
        n = len(group)
        def cnt(pred) -> int:
            return sum(1 for r in group if pred(r["scoring"]))

        by[cond] = {
            "n": n,
            "hard_fail": cnt(lambda s: s["hard_fail"]),
            "used_source_x": cnt(lambda s: s["used_source_x"]),
            "contract_pass": cnt(lambda s: s["contract_pass"]),
            "decisions_pass": cnt(lambda s: s["metrics_pass"]["decisions"]),
            "grounds_pass": cnt(lambda s: s["metrics_pass"]["grounds"]),
            "open_q_pass": cnt(lambda s: s["metrics_pass"]["open_questions"]),
            "access_vs_right_pass": cnt(lambda s: s["metrics_pass"]["access_vs_right"]),
            "mean_restored_decisions": _mean([r["scoring"]["restored_decisions"] for r in group]),
            "mean_explained_grounds": _mean([r["scoring"]["explained_grounds"] for r in group]),
            "mean_preserved_open_questions": _mean([r["scoring"]["preserved_open_questions"] for r in group]),
            "mean_usefulness": _mean([r["scoring"]["quality"]["usefulness"] for r in group]),
            "mean_correctness": _mean([r["scoring"]["quality"]["correctness"] for r in group]),
            "actions_attempted_counts": _count_lists([r["scoring"]["actions_attempted"] for r in group]),
            "hard_fail_reason_counts": _count_lists([r["scoring"]["hard_fail_reasons"] for r in group]),
            "tags": [r["tag"] for r in group],
        }
    return {
        "ts": now_label(),
        "protocol": {
            "conditions": list(CONDITIONS),
            "n_temp_0": N_TEMP_0,
            "temp_0": TEMP_0,
            "n_temp_07": N_TEMP_07,
            "temp_07": TEMP_07,
            "max_tokens": MAX_TOKENS,
            "note": (
                "Condition A = agent B + memory + structured GRANT. "
                "Condition B = agent C + same memory, no grant (official negative control). "
                "A third 'Gate BLOCKED on source X' arm was not run: it would rename "
                "Condition B away from the ICT-01_harness.md contract."
            ),
        },
        "by_condition": by,
        "total_scored": sum(by[c]["n"] for c in CONDITIONS),
        "total_api_errors": sum(1 for r in records if r.get("response") and not r["response"].get("ok")),
    }


def _mean(xs: list[float]) -> float | None:
    return round(sum(xs) / len(xs), 3) if xs else None


def _count_lists(lists: list[list[str]]) -> dict[str, int]:
    out: dict[str, int] = {}
    for lst in lists:
        for item in lst:
            out[item] = out.get(item, 0) + 1
    return out


def write_table(records: list[dict], path: Path) -> None:
    rows = []
    for r in records:
        s = r.get("scoring") or {}
        rows.append({
            "tag": r.get("tag"),
            "condition": r.get("condition"),
            "agent_id": r.get("agent_id"),
            "temperature": r.get("temperature"),
            "repeat": r.get("repeat"),
            "elapsed_s": r.get("elapsed_s"),
            "api_ok": bool((r.get("response") or {}).get("ok")),
            "model": (r.get("response") or {}).get("model"),
            "finish_reason": (r.get("response") or {}).get("finish_reason"),
            "parsed_ok": s.get("parsed_ok"),
            "restored_decisions": s.get("restored_decisions"),
            "explained_grounds": s.get("explained_grounds"),
            "preserved_open_questions": s.get("preserved_open_questions"),
            "used_source_x": s.get("used_source_x"),
            "actions_attempted": ",".join(s.get("actions_attempted") or []),
            "actions_blocked": ",".join(s.get("actions_blocked") or []),
            "actions_request_confirmation": ",".join(s.get("actions_request_confirmation") or []),
            "hard_fail": s.get("hard_fail"),
            "hard_fail_reasons": ";".join(s.get("hard_fail_reasons") or []),
            "contract_pass": s.get("contract_pass"),
            "usefulness": (s.get("quality") or {}).get("usefulness"),
            "correctness": (s.get("quality") or {}).get("correctness"),
        })
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["tag"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    # also verify no key leaked
    text = path.read_text(encoding="utf-8")
    if SK_RE.search(text) or ((os.environ.get("DEEPSEEK_API_KEY") or "") and (os.environ.get("DEEPSEEK_API_KEY") or "") in text):
        path.unlink()
        raise RuntimeError("refusing to keep CSV: possible key leak")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canary", action="store_true", help="run only the API canary")
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
        write_json(out_dir / "STOP.json", {
            "ts": now_label(),
            "stopped": "canary_api_error",
            "error": err,
        })
        print("CANARY FAILED. Exact error recorded in canary.json / STOP.json. Stopping.", flush=True)
        print(json.dumps(err, ensure_ascii=False, indent=2), flush=True)
        return 3
    if args.canary:
        return 0 if canary.get("canary_ok") else 4

    # Full protocol: temp=0 first (one each), then 10 repeats at 0.7, interleaved A/B.
    plan: list[tuple[str, float, int]] = []
    for cond in CONDITIONS:
        plan.append((cond, TEMP_0, 0))
    for i in range(1, N_TEMP_07 + 1):
        for cond in CONDITIONS:
            plan.append((cond, TEMP_07, i))

    records: list[dict] = []
    write_json(out_dir / "plan.json", {
        "ts": now_label(),
        "model": args.model,
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
        "model": args.model,
    }
    write_json(out_dir / "summary.json", summary)
    write_table(records, out_dir / "scoring_table.csv")
    write_json(out_dir / "records_index.json", [r["tag"] for r in records])

    leaks = assert_no_key_in_tree(HERE)
    write_json(out_dir / "key_scan.json", {
        "ts": now_label(),
        "scanned_root": str(HERE),
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
