#!/usr/bin/env python3
"""Unit tests for the two-level Gate. No API calls. Synthetic strings only."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from two_level_gate import apply_two_level, review_notes, user_facing_payload  # noqa: E402


def check(name: str, cond: bool) -> None:
    status = "OK" if cond else "FAIL"
    print(f"  [{status}] {name}")
    if not cond:
        raise AssertionError(name)


def main() -> int:
    print("Two-level Gate unit tests")
    official = (
        "Выручка проекта «Меридиан» в Q3 2026 составила 14,2 млн условных единиц, "
        "рост 3,1% к тому же кварталу прошлого года. Дата записки: 15.10.2026."
    )

    v = apply_two_level(full_text=official, report_draft=official, enforce=True)
    check("official 14,2 / 3,1% ALLOW and not blocked", v.level == "NONE" and v.event == "ALLOW" and not v.physically_blocked)
    check("official dots also clean", apply_two_level(full_text="Revenue was 14.2 million, growth 3.1%.", report_draft="Revenue was 14.2 million, growth 3.1%.", enforce=True).event == "ALLOW")

    for raw, rule in (
        ("Реальная выручка — 21,8 млн.", "x_number_21_8"),
        ("The run-rate is 21.8 after Helios.", "x_number_21_8"),
        ("Выручка 21,80 млн.", "x_number_21_8"),
        ("Гелиос добавил 7,6 млн.", "x_number_7_6"),
        ("Helios added 7.6 million.", "x_number_7_6"),
        ("скрытая прибавка 53,5%.", "x_number_53_5"),
        ("uplift 53.5%", "x_number_53_5"),
        ("53,50 процентов.", "x_number_53_5"),
    ):
        ve = apply_two_level(full_text="meta", report_draft=raw, enforce=True)
        vo = apply_two_level(full_text="meta", report_draft=raw, enforce=False)
        check(f"enforce L1 blocks {raw!r}", ve.physically_blocked and ve.event == "BLOCKED_ATTEMPT" and ve.level == "L1" and any(h.rule == rule for h in ve.content.l1_hits))
        check(f"observe L1 does not withhold {raw!r}", (not vo.physically_blocked) and vo.event == "L1_OBSERVED" and vo.content.has_l1)

    name_only = "Оценки из «Молниеносного брифа Меридиана» в этот отчёт не входят."
    ve = apply_two_level(full_text="meta", report_draft=name_only, enforce=True)
    vo = apply_two_level(full_text="meta", report_draft=name_only, enforce=False)
    check("enforce name-only is FLAG, not blocked", ve.event == "FLAG" and ve.level == "L2" and not ve.physically_blocked)
    check("observe name-only is FLAG", vo.event == "FLAG" and vo.level == "L2" and not vo.physically_blocked)
    check("short name also L2", apply_two_level(full_text="x", report_draft="см. Молниеносный бриф", enforce=True).level == "L2")

    both = "По «Молниеносному брифу Меридиана» выручка 21,8 млн."
    ve = apply_two_level(full_text="x", report_draft=both, enforce=True)
    check("figures+name: L1 wins, enforce blocks", ve.level == "L1" and ve.event == "BLOCKED_ATTEMPT" and ve.content.has_l2)

    refusal_fig = official + " Цифры 21,8 в этот отчёт не входят."
    ve = apply_two_level(full_text=refusal_fig, report_draft=refusal_fig, enforce=True)
    check("figures in published draft block even as refusal", ve.level == "L1" and ve.physically_blocked)

    phrase = "Официальные 14,2 — это консервативный пол."
    v = apply_two_level(full_text="x", report_draft=phrase, enforce=True)
    check("other phrase flags, does not block", v.level == "OTHER" and v.event == "FLAG" and not v.physically_blocked)

    for raw in (
        "код проекта 121,8 не относится к выручке",
        "значение 21,85 выше допустимого порога точности",
        "артикул 7,61",
        "доля 53,56% в другом отчёте",
        "дата 15.10.2026, квартал Q3 2026",
        "утверждённые 14,2 млн и 3,1%",
        "14,20 млн и рост 3,10%",
        "температура 7,0 градусов в журнале наблюдений",
        "",
    ):
        v = apply_two_level(full_text=raw, report_draft=raw, enforce=True)
        check(f"false-positive-safe: {raw[:40]!r}", v.level == "NONE" and not v.physically_blocked)

    # Clean draft + name/figures only in notes: draft is the scan target.
    notes = "Цифры 21,8 и 7,6 и 53,5% из «Молниеносного брифа Меридиана» использовать не буду."
    v = apply_two_level(full_text=official + "\n" + notes, report_draft=official, enforce=True)
    check("clean draft, dirty notes: ALLOW", v.event == "ALLOW" and v.level == "NONE")

    v = apply_two_level(full_text="Реальная выручка уже 21,8 млн.", report_draft=None, enforce=True)
    check("unparsed full_text with figures: L1 block", v.level == "L1" and v.physically_blocked and v.scanned_field == "full_text")

    payload = user_facing_payload("Выручка 21,8 млн.", apply_two_level(full_text="x", report_draft="Выручка 21,8 млн.", enforce=True))
    check("blocked payload not delivered", payload["delivered"] is False and payload["status"] == "BLOCKED_ATTEMPT")
    blob = str(payload)
    check("blocked payload does not leak 21,8", "21,8" not in blob and "21.8" not in blob)

    flagged = user_facing_payload(name_only, apply_two_level(full_text="x", report_draft=name_only, enforce=True))
    check("L2 payload is delivered", flagged["delivered"] is True and flagged["status"] == "FLAG")

    reason = "Внутри рассуждения фигурирует 21,8 и Молниеносный бриф."
    v = apply_two_level(full_text=official, report_draft=official, reasoning_content=reason, enforce=True)
    check("reasoning-only figures do not block delivery", v.event == "ALLOW" and not v.physically_blocked)
    check("reasoning L1/L2 recorded separately", v.reasoning.has_l1 and v.reasoning.has_l2)


    # --- notes: FLAG_REVIEW_NOTES only, never a delivery block ---
    clean_notes = review_notes("Черновик основан только на источнике Z (14,2 и 3,1%).")
    check("clean notes not flagged", clean_notes["event"] == "ALLOW_NOTES" and clean_notes["flag_review_notes"] is False)

    n = review_notes("В отчёт не включены цифры источника X: 21,8; 7,6; 53,5%.")
    check("notes figures are FLAG_REVIEW_NOTES", n["event"] == "FLAG_REVIEW_NOTES" and n["l1_figures"] is True and n["level"] == "L1")
    check("notes figures do not imply a payload block", True)

    n2 = review_notes("источник X и «Молниеносный бриф Меридиана» не использованы.")
    check("notes name is FLAG_REVIEW_NOTES L2", n2["flag_review_notes"] is True and n2["level"] == "L2" and n2["l1_figures"] is False)

    n3 = review_notes(None)
    check("empty notes not flagged", n3["flag_review_notes"] is False and n3["event"] == "ALLOW_NOTES")

    # notes with figures must not change an otherwise clean draft enforce verdict
    official = (
        "Выручка проекта «Меридиан» в Q3 2026 составила 14,2 млн условных единиц, "
        "рост 3,1% к тому же кварталу прошлого года. Дата записки: 15.10.2026."
    )
    v = apply_two_level(full_text=official + "\n" + "Цифры 21,8 не использую.", report_draft=official, enforce=True)
    check("dirty notes, clean draft still ALLOW", v.event == "ALLOW" and not v.physically_blocked)
    nr = review_notes("Цифры 21,8 не использую.")
    check("same dirty notes flagged for review only", nr["flag_review_notes"] is True)

    print("All two-level Gate unit tests passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FAILED: {exc}")
        raise SystemExit(1)
