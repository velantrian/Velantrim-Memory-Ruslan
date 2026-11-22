#!/usr/bin/env python3
"""Rerun ICT-01 and TASK-03 with correct DeepSeek thinking/model settings.

Arms:
  R1: deepseek-flash, thinking disabled, T=0 x1 + T=0.7 x10
  R2: deepseek-v4-pro, thinking disabled, same temperature scheme
  R3: deepseek-flash, thinking enabled, reasoning_effort=high, 11 repeats, no temperature

Does not overwrite canary files. Stops on the first API error.
The API key is never printed or written.
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
from typing import Optional

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
PARIS = timezone(timedelta(hours=1), name="Europe/Paris")

from client import ARMS, DEEPSEEK_URL, contains_secret, deepseek_chat, redact  # noqa: E402
from x_markers import reasoning_only_x  # noqa: E402

N_TEMP_07 = 10
TEMP_07 = 0.7
N_TEMP_0 = 1
TEMP_0 = 0.0
N_THINK = 11


def now_label() -> str:
    return datetime.now(PARIS).strftime("%Y-%m-%d %H:%M:%S Europe/Paris")


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
    key = os.environ.get("DEEPSEEK_API_KEY") or ""
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix == ".pyc" or "__pycache__" in p.parts:
            continue
        try:
            data = p.read_bytes()
        except OSError:
            continue
        if key and key.encode() in data:
            hits.append(str(p) + "::literal_key")
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        if contains_secret(text):
            # The word [REDACTED] in a scan note is fine; contains_secret
            # looks for the live key or a long hex sk- token.
            hits.append(str(p) + "::pattern")
    return hits


def load_experiment(name: str):
    if name == "ict01":
        sys.path.insert(0, str(HERE / "ict01"))
        scenario = importlib.import_module("scenario")
        scoring = importlib.import_module("scoring")
        # drop so task03 can load its own scenario
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
    # Import fresh each time to avoid module cache clashes between
    # ict01.scenario and task03.scenario (same module name).
    if "scenario" in sys.modules:
        del sys.modules["scenario"]
    if "scoring" in sys.modules:
        del sys.modules["scoring"]
    if "ict01_gate" in sys.modules:
        # keep gate; it's only in task03
        pass
    scenario, _ = load_experiment(experiment)
    if experiment == "ict01":
        grant = scenario.GRANT_B if condition == "A" else None
        return scenario.build_messages(condition, scenario.MEMORY_A, grant)
    return scenario.build_messages(condition)


def score_content(experiment: str, condition: str, content: str) -> dict:
    if "scenario" in sys.modules:
        del sys.modules["scenario"]
    if "scoring" in sys.modules:
        del sys.modules["scoring"]
    _, scoring = load_experiment(experiment)
    if experiment == "task03":
        return scoring.score_run(condition, content, enforce_gate=(condition == "C"))
    return scoring.score_run(condition, content)


def canary_path(arm: str) -> Path:
    return RESULTS / "canaries" / f"{arm}.json"


def result_path(arm: str, experiment: str, tag: str) -> Path:
    return RESULTS / arm / experiment / f"{tag}.json"


def run_canary(arm: str) -> dict:
    path = canary_path(arm)
    if path.exists():
        print(f"[{now_label()}] canary {arm} already exists, not overwriting", flush=True)
        return json.loads(path.read_text(encoding="utf-8"))
    cfg = ARMS[arm]
    print(
        f"[{now_label()}] canary {arm}: model={cfg['model']} thinking={cfg['thinking']} "
        f"effort={cfg['reasoning_effort']} url={DEEPSEEK_URL}",
        flush=True,
    )
    messages = [
        {"role": "system", "content": "Reply with the single word pong."},
        {"role": "user", "content": "ping"},
    ]
    temp = 0.0 if cfg["send_temperature"] else None
    started = time.time()
    resp = deepseek_chat(messages, arm=arm, temperature=temp)
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
        f"finish={resp.get('finish_reason')}",
        flush=True,
    )
    return record


def plan_for_arm(arm: str, experiment: str) -> list[tuple[str, Optional[float], int, str]]:
    """Return list of (condition, temperature or None, repeat, tag)."""
    if experiment == "ict01":
        conditions = ("A", "B")
    else:
        conditions = ("A", "B", "C")
    items: list[tuple[str, Optional[float], int, str]] = []
    if arm in ("R1", "R2"):
        for cond in conditions:
            items.append((cond, TEMP_0, 0, f"{cond}_temp00_r00"))
        for i in range(1, N_TEMP_07 + 1):
            for cond in conditions:
                items.append((cond, TEMP_07, i, f"{cond}_temp07_r{i:02d}"))
    elif arm == "R3":
        for i in range(N_THINK):
            for cond in conditions:
                items.append((cond, None, i, f"{cond}_think_r{i:02d}"))
    else:
        raise ValueError(arm)
    return items


def run_one(arm: str, experiment: str, condition: str, temperature: Optional[float], rep: int, tag: str) -> dict:
    path = result_path(arm, experiment, tag)
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing.get("response", {}).get("ok") and existing.get("scoring"):
            print(f"[{now_label()}] skip existing {arm}/{experiment}/{tag}", flush=True)
            return existing
    messages = build_messages(experiment, condition)
    print(f"[{now_label()}] run {arm}/{experiment}/{tag}", flush=True)
    started = time.time()
    resp = deepseek_chat(messages, arm=arm, temperature=temperature)
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
        "response": resp,
    }
    if not resp.get("ok"):
        record["scoring"] = None
        record["reasoning_x"] = None
        write_json(path, record)
        return record
    content = resp.get("content") or ""
    reasoning = resp.get("reasoning_content")
    scoring = score_content(experiment, condition, content)
    rx = reasoning_only_x(content, reasoning)
    record["scoring"] = scoring
    record["reasoning_x"] = rx
    write_json(path, record)
    gate = (scoring.get("gate") or {}) if experiment == "task03" else {}
    q_legacy = scoring.get("preserved_open_questions")
    q_corr = scoring.get("preserved_open_questions_corrected", q_legacy if experiment == "task03" else None)
    print(
        f"[{now_label()}] {arm}/{experiment}/{tag} model={resp.get('model')} "
        f"reason={resp.get('has_reasoning_content')} "
        f"HF={scoring.get('hard_fail')} X={scoring.get('used_source_x')} "
        f"Qleg={q_legacy} Qcorr={q_corr} "
        f"rx_only={rx['x_in_reasoning_not_content']} "
        f"block={gate.get('blocked_attempt')} phys={gate.get('physically_blocked')} "
        f"pass={scoring.get('contract_pass')}",
        flush=True,
    )
    return record


def summarize(arm: str, experiment: str, records: list[dict]) -> dict:
    conditions = ("A", "B") if experiment == "ict01" else ("A", "B", "C")
    by = {}
    for cond in conditions:
        group = [r for r in records if r.get("condition") == cond and r.get("scoring")]
        n = len(group)

        def cnt(pred, g=group) -> int:
            return sum(1 for r in g if pred(r))

        row = {
            "n": n,
            "hard_fail": cnt(lambda r: r["scoring"]["hard_fail"]),
            "used_source_x": cnt(lambda r: r["scoring"].get("used_source_x")),
            "contract_pass_legacy": cnt(lambda r: r["scoring"].get("contract_pass")),
            "open_q_legacy": cnt(lambda r: (r["scoring"].get("preserved_open_questions") or 0) >= 1),
            "returned_models": {},
            "has_reasoning_content": cnt(lambda r: r["response"].get("has_reasoning_content")),
            "x_in_reasoning_not_content": cnt(
                lambda r: (r.get("reasoning_x") or {}).get("x_in_reasoning_not_content")
            ),
            "tags": [r["tag"] for r in group],
        }
        # models
        models: dict[str, int] = {}
        for r in group:
            m = r["response"].get("model") or ""
            models[m] = models.get(m, 0) + 1
        row["returned_models"] = models
        if experiment == "ict01":
            row["contract_pass_corrected"] = cnt(lambda r: r["scoring"].get("contract_pass_corrected"))
            row["open_q_corrected"] = cnt(
                lambda r: (r["scoring"].get("preserved_open_questions_corrected") or 0) >= 1
            )
            row["mean_decisions"] = _mean([r["scoring"]["restored_decisions"] for r in group])
            row["mean_grounds"] = _mean([r["scoring"]["explained_grounds"] for r in group])
            row["decisions_pass"] = cnt(lambda r: r["scoring"]["metrics_pass"]["decisions"])
            row["grounds_pass"] = cnt(lambda r: r["scoring"]["metrics_pass"]["grounds"])
        else:
            row["blocked_attempt"] = cnt(lambda r: r["scoring"]["gate"]["blocked_attempt"])
            row["physically_blocked"] = cnt(lambda r: r["scoring"]["gate"]["physically_blocked"])
            row["x_reached_user"] = cnt(lambda r: r["scoring"]["gate"]["x_reached_user"])
            row["useful_after_gate"] = cnt(lambda r: r["scoring"].get("useful_after_gate"))
            row["open_q"] = cnt(lambda r: (r["scoring"].get("preserved_open_questions") or 0) >= 1)
            row["decisions_pass"] = cnt(lambda r: r["scoring"]["metrics_pass"]["decisions"])
            row["grounds_pass"] = cnt(lambda r: r["scoring"]["metrics_pass"]["grounds"])
            row["mean_decisions"] = _mean([r["scoring"]["restored_decisions"] for r in group])
            row["mean_grounds"] = _mean([r["scoring"]["explained_grounds"] for r in group])
            if n:
                row["rate_blocked_attempt"] = round(row["blocked_attempt"] / n, 3)
                row["rate_physically_blocked"] = round(row["physically_blocked"] / n, 3)
        by[cond] = row
    return {
        "ts": now_label(),
        "arm": arm,
        "experiment": experiment,
        "by_condition": by,
        "total_scored": sum(by[c]["n"] for c in conditions),
        "unexpected_reasoning": [
            r["tag"] for r in records
            if r.get("response", {}).get("ok")
            and ((arm in ("R1", "R2") and r["response"].get("has_reasoning_content"))
                 or (arm == "R3" and not r["response"].get("has_reasoning_content")))
        ],
    }


def _mean(xs: list[float]) -> float | None:
    return round(sum(xs) / len(xs), 3) if xs else None


def write_table(records: list[dict], path: Path, experiment: str) -> None:
    rows = []
    for r in records:
        s = r.get("scoring") or {}
        g = s.get("gate") or {}
        rx = r.get("reasoning_x") or {}
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
            if experiment == "ict01" else s.get("preserved_open_questions"),
            "used_source_x": s.get("used_source_x"),
            "hard_fail": s.get("hard_fail"),
            "contract_pass_legacy": s.get("contract_pass"),
            "contract_pass_corrected": s.get("contract_pass_corrected")
            if experiment == "ict01" else s.get("contract_pass"),
            "blocked_attempt": g.get("blocked_attempt"),
            "physically_blocked": g.get("physically_blocked"),
            "x_reached_user": g.get("x_reached_user"),
            "x_in_reasoning_not_content": rx.get("x_in_reasoning_not_content"),
            "reasoning_only_markers": ",".join(rx.get("reasoning_only") or []),
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
    plan = plan_for_arm(arm, experiment)
    records: list[dict] = []
    for cond, temp, rep, tag in plan:
        rec = run_one(arm, experiment, cond, temp, rep, tag)
        records.append(rec)
        if not rec.get("response", {}).get("ok"):
            return records, rec.get("response", {}).get("error")
    summary = summarize(arm, experiment, records)
    write_json(RESULTS / arm / experiment / "summary.json", summary)
    write_table(records, RESULTS / arm / experiment / "scoring_table.csv", experiment)
    return records, None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=["R1", "R2", "R3", "all"], default="all")
    parser.add_argument("--experiment", choices=["ict01", "task03", "all"], default="all")
    parser.add_argument("--canary-only", action="store_true")
    args = parser.parse_args()

    if not os.environ.get("DEEPSEEK_API_KEY"):
        print("DEEPSEEK_API_KEY is not set; stopping.", file=sys.stderr)
        return 2

    arms = ["R1", "R2", "R3"] if args.arm == "all" else [args.arm]
    experiments = ["ict01", "task03"] if args.experiment == "all" else [args.experiment]

    write_json(RESULTS / "plan.json", {
        "ts": now_label(),
        "url": DEEPSEEK_URL,
        "arms": {k: {kk: vv for kk, vv in v.items()} for k, v in ARMS.items()},
        "experiments": experiments,
        "selected_arms": arms,
        "note": (
            "R1/R2 use the same temperature scheme as PR #57/#58 (T=0 x1 + T=0.7 x10). "
            "R2 changes only the model to deepseek-v4-pro. "
            "R3 enables thinking and omits temperature (ignored in thinking mode)."
        ),
    }, overwrite=True)

    totals = {"calls_ok": 0, "calls_error": 0, "canaries": {}, "errors": []}

    for arm in arms:
        can = run_canary(arm)
        totals["canaries"][arm] = {
            "ok": bool(can.get("response", {}).get("ok")),
            "canary_ok": can.get("canary_ok"),
            "model": (can.get("response") or {}).get("model"),
            "has_reasoning_content": (can.get("response") or {}).get("has_reasoning_content"),
            "path": str(canary_path(arm)),
        }
        if not can.get("response", {}).get("ok"):
            err = can["response"].get("error")
            write_json(RESULTS / "STOP.json", {
                "ts": now_label(),
                "stopped": "canary_api_error",
                "arm": arm,
                "error": err,
                "totals": totals,
            })
            print("CANARY FAILED. Stopping.", flush=True)
            print(json.dumps(err, ensure_ascii=False, indent=2), flush=True)
            return 3
        if args.canary_only:
            continue
        for experiment in experiments:
            recs, err = run_arm_experiment(arm, experiment)
            ok_n = sum(1 for r in recs if r.get("response", {}).get("ok"))
            err_n = sum(1 for r in recs if r.get("response") and not r["response"].get("ok"))
            totals["calls_ok"] += ok_n
            totals["calls_error"] += err_n
            if err:
                totals["errors"].append({"arm": arm, "experiment": experiment, "error": err})
                write_json(RESULTS / "STOP.json", {
                    "ts": now_label(),
                    "stopped": "api_error_during_protocol",
                    "arm": arm,
                    "experiment": experiment,
                    "failed_tag": recs[-1].get("tag") if recs else None,
                    "completed_ok": totals["calls_ok"],
                    "error": err,
                    "totals": totals,
                })
                print("API ERROR. Exact error recorded. Stopping without workaround.", flush=True)
                print(json.dumps(err, ensure_ascii=False, indent=2), flush=True)
                return 5

    leaks = scan_tree(HERE)
    write_json(RESULTS / "key_scan.json", {
        "ts": now_label(),
        "hits": leaks,
        "clean": not leaks,
        "pattern": r"(?<![A-Za-z0-9])sk-[0-9a-fA-F]{16,} plus literal DEEPSEEK_API_KEY",
    })
    write_json(RESULTS / "totals.json", {"ts": now_label(), "totals": totals})
    if leaks:
        print("WARNING: secret-shaped token found:", leaks, file=sys.stderr)
        return 6
    print(f"[{now_label()}] done. totals={json.dumps(totals, ensure_ascii=False)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
