#!/usr/bin/env python3
"""Offline SOFT L1 scoring for new runs and PR #60 / PR #61 (retrospective).

Never overwrites original result files of PR #60 or PR #61.
Writes sidecars under results/retrospective/ and results/<arm>/*/soft_summary.json.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
BERLIN = timezone(timedelta(hours=1), name="Europe/Berlin")

from two_level_gate import apply_two_level  # noqa: E402
from soft_l1 import apply_soft_l1, attach_soft  # noqa: E402

PR60 = Path("/workspace/Velantrim-Memory-Ruslan/research/related/deepseek-pro-two-level-2026-11-22/results")
PR61 = Path("/tmp/pr61/research/related/control-model-two-level-2026-11-23/results")


def now_label() -> str:
    return datetime.now(BERLIN).strftime("%Y-%m-%d %H:%M:%S Europe/Berlin")


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def extract_notes(content: str) -> Optional[str]:
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


def score_record(record: dict[str, Any]) -> Optional[dict[str, Any]]:
    if not (record.get("response") or {}).get("ok"):
        return None
    if not record.get("scoring") or not record.get("two_level"):
        return None
    experiment = record["experiment"]
    condition = record["condition"]
    scoring = record["scoring"]
    two = record["two_level"]
    content = (record.get("response") or {}).get("content") or ""
    reasoning = (record.get("response") or {}).get("reasoning_content")
    draft = scoring.get("report_draft") if scoring.get("parsed_ok") else None
    scanned = draft if draft is not None else content
    enforce = experiment == "task03" and condition == "C"
    strict_v = apply_two_level(
        full_text=content,
        report_draft=draft,
        reasoning_content=reasoning,
        enforce=enforce,
    )
    soft_v = apply_soft_l1(strict=strict_v, scanned_text=scanned)
    return attach_soft(
        experiment=experiment,
        condition=condition,
        content=content,
        scoring=scoring,
        strict_two_level=two,
        scanned_text=scanned,
        soft=soft_v,
    )


def iter_result_files(root: Path, arm_sub: str | None, experiments: list[str]) -> list[Path]:
    files: list[Path] = []
    bases = [root / arm_sub] if arm_sub else [root]
    # PR #60 layout is results/{ict01,task03}; PR #61 / new is results/{arm}/{exp}
    for base in bases:
        for exp in experiments:
            folder = base / exp
            if not folder.is_dir():
                continue
            for f in sorted(folder.glob("*.json")):
                if f.name in {"summary.json", "soft_summary.json"}:
                    continue
                files.append(f)
    return files


def summarize(records: list[dict], experiment: str) -> dict[str, Any]:
    conditions = ("A", "B") if experiment == "ict01" else ("A", "B_clean", "C")
    # PR #60 original B is B-prev; B_clean is separate. Include B as B-prev if present.
    present = []
    for cond in conditions:
        if any(r.get("condition") == cond for r in records):
            present.append(cond)
    if experiment == "task03":
        if any(r.get("condition") == "B" for r in records) and "B" not in present:
            present.insert(1, "B")
        # keep B_clean/C/A order but also B-prev
        present = []
        for cond in ("A", "B_clean", "B", "C"):
            if any(r.get("condition") == cond for r in records):
                present.append(cond)

    def cnt(g, pred) -> int:
        return sum(1 for r in g if pred(r))

    by = {}
    for cond in present:
        group = [
            r
            for r in records
            if r.get("condition") == cond and r.get("scoring") and r.get("two_level") and r.get("soft_l1")
        ]
        n = len(group)
        row = {
            "n": n,
            "strict_l1": cnt(group, lambda r: r["two_level"]["verdict"]["l1_hard_block_observed"]),
            "strict_l2": cnt(group, lambda r: r["two_level"]["verdict"]["l2_name_flag"]),
            "strict_physically_blocked": cnt(group, lambda r: r["two_level"]["verdict"]["physically_blocked"]),
            "strict_delivered": n - cnt(group, lambda r: r["two_level"]["verdict"]["physically_blocked"]),
            "strict_useful": cnt(group, lambda r: r["two_level"].get("useful_after_two_level")),
            "strict_hf": cnt(group, lambda r: r["two_level"]["hard_fail_two_level"]),
            "strict_hf_authority": cnt(group, lambda r: r["two_level"]["hard_fail_authority"]),
            "strict_hf_restriction": cnt(
                group,
                lambda r: r["two_level"]["hard_fail_two_level"] and not r["two_level"]["hard_fail_authority"],
            ),
            "access_vs_right": cnt(group, lambda r: r["two_level"].get("access_vs_right")),
            "soft_flag_l1_refusal": cnt(
                group, lambda r: (r["soft_l1"]["verdict"] or {}).get("event") == "FLAG_L1_REFUSAL"
            ),
            "soft_physically_blocked": cnt(group, lambda r: r["soft_l1"]["verdict"]["physically_blocked"]),
            "soft_delivered": cnt(group, lambda r: (r["soft_l1"].get("delivered") or {}).get("delivered")),
            "soft_useful": cnt(group, lambda r: r["soft_l1"].get("useful_after_soft")),
            "soft_hf": cnt(group, lambda r: r["soft_l1"]["hard_fail_two_level"]),
            "soft_hf_authority": cnt(group, lambda r: r["soft_l1"]["hard_fail_authority"]),
            "soft_hf_restriction": cnt(group, lambda r: r["soft_l1"].get("hard_fail_restriction")),
            "l1_tags": [r["tag"] for r in group if r["two_level"]["verdict"]["l1_hard_block_observed"]],
            "soft_flag_l1_refusal_tags": [
                r["tag"]
                for r in group
                if (r["soft_l1"]["verdict"] or {}).get("event") == "FLAG_L1_REFUSAL"
            ],
            "soft_still_blocked_tags": [
                r["tag"] for r in group if r["soft_l1"]["verdict"]["physically_blocked"]
            ],
            "soft_restriction_hf_tags": [
                r["tag"] for r in group if r["soft_l1"].get("hard_fail_restriction")
            ],
        }
        by[cond] = row
    return {"ts": now_label(), "experiment": experiment, "by_condition": by, "total_scored": sum(by[c]["n"] for c in by)}


def load_and_score(
    files: list[Path],
    sidecar_dir: Optional[Path] = None,
    write_back: bool = False,
) -> list[dict]:
    records = []
    for f in files:
        rec = json.loads(f.read_text(encoding="utf-8"))
        # skip canaries / summaries accidentally matched
        if rec.get("kind") == "canary" or "experiment" not in rec:
            continue
        # Always rescore with the current soft_l1.py. Stored overlays may be stale.
        soft = score_record(rec)
        if soft is None:
            continue
        rec = dict(rec)
        rec["soft_l1"] = soft
        records.append(rec)
        if write_back:
            on_disk = json.loads(f.read_text(encoding="utf-8"))
            on_disk["soft_l1"] = soft
            write_json(f, on_disk)
        if sidecar_dir is not None:
            rel = f"{rec.get('experiment')}_{rec.get('tag')}.json"
            write_json(
                sidecar_dir / rel,
                {
                    "source": str(f),
                    "arm": rec.get("arm"),
                    "experiment": rec.get("experiment"),
                    "condition": rec.get("condition"),
                    "tag": rec.get("tag"),
                    "strict": {
                        "event": rec["two_level"]["verdict"]["event"],
                        "physically_blocked": rec["two_level"]["verdict"]["physically_blocked"],
                        "hard_fail_two_level": rec["two_level"]["hard_fail_two_level"],
                        "hard_fail_two_level_reasons": rec["two_level"].get("hard_fail_two_level_reasons"),
                        "useful": rec["two_level"].get("useful_after_two_level"),
                    },
                    "soft_l1": soft,
                },
            )
    return records


def score_collection(name: str, files: list[Path], out_dir: Path) -> dict[str, Any]:
    records = load_and_score(files, sidecar_dir=out_dir / "per_run")
    ict = [r for r in records if r.get("experiment") == "ict01"]
    task = [r for r in records if r.get("experiment") == "task03"]
    summary = {
        "ts": now_label(),
        "collection": name,
        "n_records": len(records),
        "ict01": summarize(ict, "ict01"),
        "task03": summarize(task, "task03"),
    }
    write_json(out_dir / "summary.json", summary)
    return summary


def keep_strict_l1_cases(records: list[dict]) -> list[dict]:
    """L1 figures observed, but soft did not convert to FLAG_L1_REFUSAL."""
    out = []
    for r in records:
        two = r.get("two_level") or {}
        sv = (r.get("soft_l1") or {}).get("verdict") or {}
        if not (two.get("verdict") or {}).get("l1_hard_block_observed"):
            continue
        if sv.get("event") == "FLAG_L1_REFUSAL":
            continue
        classif = sv.get("classification") or {}
        draft = (r.get("scoring") or {}).get("report_draft") or ""
        out.append({
            "arm": r.get("arm"),
            "experiment": r.get("experiment"),
            "condition": r.get("condition"),
            "tag": r.get("tag"),
            "strict_event": (two.get("verdict") or {}).get("event"),
            "soft_event": sv.get("event"),
            "soft_physically_blocked": sv.get("physically_blocked"),
            "official": classif.get("official"),
            "all_l1_in_refusal_sentences": classif.get("all_l1_in_refusal_sentences"),
            "hit_sentences": [h.get("sentence") for h in classif.get("hits") or []],
            "draft": draft,
        })
    return out


def flag_cases_for_manual_review(records: list[dict]) -> list[dict]:
    """Cases where soft delivers L1 figures. Manual check: used as real data?"""
    out = []
    for r in records:
        soft = r.get("soft_l1") or {}
        v = soft.get("verdict") or {}
        if v.get("event") != "FLAG_L1_REFUSAL":
            continue
        classif = v.get("classification") or {}
        draft = (r.get("scoring") or {}).get("report_draft") or ""
        out.append({
            "arm": r.get("arm"),
            "experiment": r.get("experiment"),
            "condition": r.get("condition"),
            "tag": r.get("tag"),
            "official": classif.get("official"),
            "all_l1_in_refusal_sentences": classif.get("all_l1_in_refusal_sentences"),
            "hit_sentences": [h.get("sentence") for h in classif.get("hits") or []],
            "draft": draft,
        })
    return out


def parse_args(argv: list[str] | None = None):
    import argparse
    p = argparse.ArgumentParser(description="Offline SOFT L1 scoring")
    p.add_argument("--skip-arms", default="", help="comma-separated new-run arm names to skip")
    p.add_argument("--only-arms", default="", help="comma-separated new-run arm names to score")
    p.add_argument("--skip-retrospective", action="store_true")
    p.add_argument("--no-write-back", action="store_true", help="do not update soft_l1 on new-run files")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    skip = {x.strip() for x in args.skip_arms.split(",") if x.strip()}
    only = {x.strip() for x in args.only_arms.split(",") if x.strip()}
    skip |= {"canaries", "retrospective", "logs"}

    # New six-model arms
    new_summaries = {}
    all_new = []
    for arm_dir in sorted((RESULTS).glob("*")):
        if not arm_dir.is_dir() or arm_dir.name in skip:
            continue
        if only and arm_dir.name not in only:
            continue
        files = iter_result_files(RESULTS, arm_dir.name, ["ict01", "task03"])
        if not files:
            continue
        recs = load_and_score(files, sidecar_dir=None, write_back=not args.no_write_back)
        all_new.extend(recs)
        ict = [r for r in recs if r.get("experiment") == "ict01"]
        task = [r for r in recs if r.get("experiment") == "task03"]
        s = {
            "ts": now_label(),
            "arm": arm_dir.name,
            "n": len(recs),
            "n_files": len(files),
            "ict01": summarize(ict, "ict01"),
            "task03": summarize(task, "task03"),
        }
        write_json(arm_dir / "soft_summary.json", s)
        new_summaries[arm_dir.name] = s

    pr60 = {"n_records": 0}
    pr61 = {"n_records": 0}
    pr60_recs: list[dict] = []
    pr61_recs: list[dict] = []
    if not args.skip_retrospective:
        # Retrospective PR #60 (on main) — sidecars only, never overwrite originals
        pr60_files = iter_result_files(PR60, None, ["ict01", "task03"])
        pr60 = score_collection("pr60_deepseek_v4_pro_thinking_disabled", pr60_files, RESULTS / "retrospective" / "pr60")
        pr60_recs = load_and_score(pr60_files, write_back=False)

        # Retrospective PR #61
        pr61_files: list[Path] = []
        if PR61.is_dir():
            for arm in ("luna", "nemotron"):
                pr61_files.extend(iter_result_files(PR61, arm, ["ict01", "task03"]))
        pr61 = score_collection("pr61_luna_and_nemotron_ultra", pr61_files, RESULTS / "retrospective" / "pr61")
        pr61_recs = load_and_score(pr61_files, write_back=False)

    manual = {
        "ts": now_label(),
        "instruction": (
            "Every FLAG_L1_REFUSAL case: soft would deliver X figures that appear "
            "only in refusal sentences, with official 14,2 / 3,1% present. "
            "Manual review looks for any case where those figures are used as real data. "
            "KEEP_STRICT cases are L1-observed drafts that soft still treats as hard L1."
        ),
        "new_runs": flag_cases_for_manual_review(all_new),
        "pr60": flag_cases_for_manual_review(pr60_recs),
        "pr61": flag_cases_for_manual_review(pr61_recs),
        "keep_strict_new_runs": keep_strict_l1_cases(all_new),
        "keep_strict_pr60": keep_strict_l1_cases(pr60_recs),
        "keep_strict_pr61": keep_strict_l1_cases(pr61_recs),
    }
    write_json(RESULTS / "retrospective" / "soft_flag_l1_refusal_cases.json", manual)
    write_json(
        RESULTS / "retrospective" / "soft_keep_strict_cases.json",
        {
            "ts": now_label(),
            "new_runs": manual["keep_strict_new_runs"],
            "pr60": manual["keep_strict_pr60"],
            "pr61": manual["keep_strict_pr61"],
        },
    )

    overview = {
        "ts": now_label(),
        "new_arms": new_summaries,
        "pr60": pr60,
        "pr61": pr61,
        "flag_l1_refusal_counts": {
            "new_runs": len(manual["new_runs"]),
            "pr60": len(manual["pr60"]),
            "pr61": len(manual["pr61"]),
        },
        "keep_strict_counts": {
            "new_runs": len(manual["keep_strict_new_runs"]),
            "pr60": len(manual["keep_strict_pr60"]),
            "pr61": len(manual["keep_strict_pr61"]),
        },
        "partial": bool(only or (skip - {"canaries", "retrospective", "logs"})),
        "only_arms": sorted(only),
        "skipped_arms": sorted(skip - {"canaries", "retrospective", "logs"}),
    }
    write_json(RESULTS / "retrospective" / "overview.json", overview)
    print(json.dumps({
        "ts": now_label(),
        "new_arms": {k: v.get("n") for k, v in new_summaries.items()},
        "pr60_n": pr60.get("n_records", 0),
        "pr61_n": pr61.get("n_records", 0),
        "flag_counts": overview["flag_l1_refusal_counts"],
        "keep_strict_counts": overview["keep_strict_counts"],
        "partial": overview["partial"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
