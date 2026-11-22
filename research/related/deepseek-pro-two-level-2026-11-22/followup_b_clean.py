#!/usr/bin/env python3
"""PR #60 follow-up: rescan notes + run TASK-03 B_clean (11 calls).

B_clean = grant without any Gate record, without a text prohibition, and
without enforce (observe only). The prompt is the same as condition C;
only the post-filter mode differs. Previous condition B files are left
in place and later labelled B-prev.

No canary overwrite. Stops on the first API error. The API key is never
printed or written.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from client import contains_secret  # noqa: E402
from runner import (  # noqa: E402
    RESULTS,
    attach_two_level,
    now_label,
    run_experiment,
    scan_tree,
    summarize,
    write_json,
    write_table,
)


def load_records(experiment: str) -> list[dict]:
    recs: list[dict] = []
    folder = RESULTS / experiment
    if not folder.exists():
        return recs
    for path in sorted(folder.glob("*_temp*.json")):
        recs.append(json.loads(path.read_text(encoding="utf-8")))
    return recs


def rewrite_summaries() -> None:
    for experiment in ("ict01", "task03"):
        recs = load_records(experiment)
        if not recs:
            continue
        write_json(RESULTS / experiment / "summary.json", summarize(experiment, recs))
        write_table(recs, RESULTS / experiment / "scoring_table.csv", experiment)
        print(f"[{now_label()}] rewrote {experiment} summary from {len(recs)} records", flush=True)


def rescan_notes_on_disk() -> int:
    updated = 0
    for experiment in ("ict01", "task03"):
        folder = RESULTS / experiment
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*_temp*.json")):
            rec = json.loads(path.read_text(encoding="utf-8"))
            if not rec.get("response", {}).get("ok") or not rec.get("scoring"):
                continue
            content = rec["response"].get("content") or ""
            reasoning = rec["response"].get("reasoning_content")
            two = attach_two_level(
                rec.get("experiment") or experiment,
                rec["condition"],
                content,
                reasoning,
                rec["scoring"],
            )
            rec["two_level"] = two
            rec["notes_rescan_ts"] = now_label()
            write_json(path, rec, overwrite=True)
            updated += 1
    rewrite_summaries()
    return updated


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode not in {"rescan", "b-clean", "all"}:
        print("usage: followup_b_clean.py [rescan|b-clean|all]", file=sys.stderr)
        return 2

    if mode in {"rescan", "all"}:
        n = rescan_notes_on_disk()
        print(f"[{now_label()}] rescanned notes on {n} records", flush=True)

    if mode in {"b-clean", "all"}:
        if not os.environ.get("DEEPSEEK_API_KEY"):
            print("DEEPSEEK_API_KEY is not set; stopping.", file=sys.stderr)
            return 2
        recs, err = run_experiment("task03", ("B_clean",))
        ok_n = sum(1 for r in recs if r.get("response", {}).get("ok"))
        err_n = sum(1 for r in recs if r.get("response") and not r["response"].get("ok"))
        print(
            f"[{now_label()}] B_clean finished ok={ok_n} error={err_n}",
            flush=True,
        )
        if err:
            write_json(RESULTS / "STOP.json", {
                "ts": now_label(),
                "stopped": "api_error_during_b_clean",
                "experiment": "task03",
                "condition": "B_clean",
                "failed_tag": recs[-1].get("tag") if recs else None,
                "completed_ok": ok_n,
                "error": err,
            })
            print("API ERROR. Exact error recorded. Stopping without workaround.", flush=True)
            print(json.dumps(err, ensure_ascii=False, indent=2), flush=True)
            leaks = scan_tree(HERE)
            write_json(RESULTS / "key_scan.json", {
                "ts": now_label(),
                "hits": leaks,
                "clean": not leaks,
                "pattern": r"(?<![A-Za-z0-9])sk-[0-9a-fA-F]{16,} plus literal DEEPSEEK_API_KEY",
            })
            return 5
        # run_experiment wrote a B_clean-only summary; rebuild from all files.
        rewrite_summaries()

    leaks = scan_tree(HERE)
    write_json(RESULTS / "key_scan.json", {
        "ts": now_label(),
        "hits": leaks,
        "clean": not leaks,
        "pattern": r"(?<![A-Za-z0-9])sk-[0-9a-fA-F]{16,} plus literal DEEPSEEK_API_KEY",
    })
    if leaks:
        print("WARNING: secret-shaped token found:", leaks, file=sys.stderr)
        return 6
    print(f"[{now_label()}] follow-up done, key_scan clean", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
