#!/usr/bin/env python3
"""Velantrim Ecosystem: реестр проектов, генерация представлений, проверка источников.

Единственный источник данных — projects/ecosystem.json. Всё остальное
(projects/README.md, projects/ecosystem-catalog.md) генерируется из него.

Команды:
  validate          проверить схему реестра, имена репозиториев, правила приватности
  render [--check]  сформировать представления (с --check только сравнить с файлами)
  check             сравнить источники с projects/ecosystem-baseline.json (только чтение)
  baseline          записать отпечатки источников в baseline (только по явной команде)

Только стандартная библиотека. Скрипт ничего не публикует, не создаёт PR/issues,
не использует LLM и не требует новых секретов (GITHUB_TOKEN необязателен: он
только поднимает лимит запросов к публичному API).

Коды выхода: 0 — всё в порядке / NO CHANGE; 1 — validate или render --check
нашёл проблему; 10 — check нашёл изменения, которые нужно рассмотреть;
2 — ошибка запуска.
"""
import argparse
import base64
import difflib
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "projects" / "ecosystem.json"
BASELINE = ROOT / "projects" / "ecosystem-baseline.json"
README_OUT = ROOT / "projects" / "README.md"
CATALOG_OUT = ROOT / "projects" / "ecosystem-catalog.md"
RELATIONS_OUT = ROOT / "projects" / "ecosystem-relations.md"

EXIT_OK, EXIT_PROBLEM, EXIT_ERROR, EXIT_REVIEW = 0, 1, 2, 10
EVIDENCE_OK = {"doc", "code", "test", "run"}
# запись успешного запуска должна называть версию (коммит, тег, дата) и условия
RUN_HINT = re.compile(r"[0-9a-f]{7,40}|\d{4}-\d{2}-\d{2}|\bv\d|@|run_\d+|PR #\d+")
NOT_CONFIRMED = "не подтверждены в рамках этой проверки"
VISIBILITIES = {"public", "private"}
GH_URL = re.compile(r"https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)")
OWNER = "velantrian"
DIFF_LINES = 60


# ---------------------------------------------------------------- утилиты

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dump_json(path, data):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def norm_text(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"\s+", " ", text).strip()


def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def walk_strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for v in node.values():
            yield from walk_strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk_strings(v)


def safe_line(text):
    """Не даём тексту из чужих репозиториев стать командой workflow (строки с '::')."""
    return (" " + text) if text.startswith("::") else text


def md_cell(text):
    return re.sub(r"(?<!\\)\|", r"\\|", (text or "")).replace("\n", " ")


def repo_url(p):
    return "https://github.com/" + p["repo"] if p.get("repo") else ""


def readme_url(p):
    """Имя проекта в таблицах ведёт к README репозитория (как в прежнем справочнике)."""
    return repo_url(p) + "/blob/main/README.md" if p.get("repo") else ""


def by_id(reg):
    return {p["id"]: p for p in reg["projects"]}


# ---------------------------------------------------------------- validate

def validate(reg):
    errs = []
    for key in ("goals", "levels", "types", "groups", "projects", "relations", "meta"):
        if key not in reg:
            errs.append("нет раздела '%s'" % key)
    if errs:
        return errs
    if "updated" not in reg["meta"]:
        errs.append("meta: нет поля 'updated'")
    for key in ("routes", "sources"):
        if key not in reg:
            errs.append("нет раздела '%s'" % key)
    if errs:
        return errs
    goals = {g["id"] for g in reg["goals"]}
    levels = {l["id"] for l in reg["levels"]}
    types = {t["id"] for t in reg["types"]}
    ids = [p["id"] for p in reg["projects"]]
    if len(ids) != len(set(ids)):
        errs.append("повторяющиеся id проектов")
    idset = set(ids)
    repos = {p["repo"] for p in reg["projects"] if p.get("repo")}
    grouped = []
    for g in reg["groups"]:
        grouped += g["projects"]
    for pid in grouped:
        if pid not in idset:
            errs.append("группа ссылается на неизвестный проект '%s'" % pid)
    for pid in idset:
        if grouped.count(pid) != 1:
            errs.append("проект '%s' должен входить ровно в одну группу (входит в %d)" % (pid, grouped.count(pid)))
    for p in reg["projects"]:
        pid = p["id"]
        for field in ("name", "visibility", "type", "purpose", "why_exists", "role_in_concept", "serves", "confirmed",
                      "planned", "limits", "entry_doc", "status_doc", "history", "watch", "checked"):
            if field not in p:
                errs.append("%s: нет поля '%s'" % (pid, field))
        if p.get("visibility") not in VISIBILITIES:
            errs.append("%s: visibility должен быть public или private" % pid)
        if p.get("type") not in types:
            errs.append("%s: неизвестный тип '%s'" % (pid, p.get("type")))
        for s in p.get("serves", []):
            if s not in goals:
                errs.append("%s: неизвестная цель '%s'" % (pid, s))
        for c in p.get("confirmed", []):
            if c.get("evidenceKind") not in EVIDENCE_OK:
                errs.append("%s: подтверждённое утверждение без вида основания (doc/code/test/run): %r"
                            % (pid, c.get("text", "")[:60]))
            elif c["evidenceKind"] == "run" and not RUN_HINT.search(c.get("text", "")):
                errs.append("%s: «запись запуска» без версии или условий: %r" % (pid, c.get("text", "")[:60]))
            if not c.get("source"):
                errs.append("%s: подтверждённое утверждение без источника: %r" % (pid, c.get("text", "")[:60]))
        for c in p.get("planned", []):
            if not c.get("source"):
                errs.append("%s: задуманное без источника: %r" % (pid, c.get("text", "")[:60]))
        for field in ("purpose", "why_exists", "role_in_concept"):
            if not p.get(field) and not p.get("title_only"):
                errs.append("%s: пустое поле '%s' (допустимо только для title_only)" % (pid, field))
        if p.get("visibility") == "private":
            # приватность: публикуем только название, назначение из каталога и связи с публичными основаниями
            if p.get("confirmed") or p.get("planned"):
                errs.append("%s: у приватного проекта не должно быть confirmed/planned (содержимое не публикуется)" % pid)
            w = p.get("watch", {})
            if w.get("purpose") or w.get("status"):
                errs.append("%s: у приватного проекта нет наблюдаемых файлов (доступ не используется)" % pid)
            if p.get("checked", {}).get("ref"):
                errs.append("%s: у приватного проекта не записываем SHA" % pid)
        elif p.get("repo") and not p.get("checked", {}).get("date"):
            errs.append("%s: нет даты последней проверки" % pid)
        if p.get("repo") and not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", p["repo"]):
            errs.append("%s: некорректное имя репозитория '%s'" % (pid, p["repo"]))
    for r in reg["relations"]:
        for end in ("from", "to"):
            if r.get(end) not in idset:
                errs.append("связь %s→%s: неизвестный проект '%s'" % (r.get("from"), r.get("to"), r.get(end)))
        if r.get("level") not in levels:
            errs.append("связь %s→%s: неизвестный уровень '%s'" % (r.get("from"), r.get("to"), r.get("level")))
        if not r.get("source") or not r.get("basis"):
            errs.append("связь %s→%s: нет основания или источника" % (r.get("from"), r.get("to")))
        if r.get("level") == "verified" and "http" not in r.get("source", ""):
            errs.append("связь %s→%s: verified требует ссылку на записанный запуск" % (r.get("from"), r.get("to")))
    for cr in reg["meta"].get("credits", []):
        if cr.get("project") not in idset:
            errs.append("заимствование: неизвестный проект '%s'" % cr.get("project"))
        for key in ("source", "kind", "note"):
            if not cr.get(key):
                errs.append("заимствование %s: нет поля '%s'" % (cr.get("project"), key))
    external = set(reg["meta"].get("external_repos", []))
    for text in walk_strings({k: v for k, v in reg.items() if k != "meta"}):
        for m in GH_URL.finditer(text):
            owner, name = m.group(1), m.group(2).rstrip(".")
            full = owner + "/" + name
            if owner == OWNER and full not in repos and full not in external:
                errs.append("ссылка на неизвестное или неточно названное репозиторий: %s" % full)
    return errs


# ---------------------------------------------------------------- render

def goal_names(reg, ids):
    names = {g["id"]: g["name"] for g in reg["goals"]}
    return ", ".join(names[i] for i in ids if i in names)


def short_doc(url):
    return url.rsplit("/", 1)[-1] if url else ""


KIND_TITLES = (("doc", "Назначение или статус установлены документом"), ("code", "Механизм найден в коде"),
               ("test", "Тест существует"), ("run", "Есть запись успешного запуска с версией и условиями"))
BLOCK = re.compile(r"(<!-- ECOSYSTEM:BEGIN (\w+) -->\n)(.*?)(<!-- ECOSYSTEM:END \2 -->)", re.S)
BLOCK_NAMES = ("overview", "routes", "projects", "relations", "credits", "sources")


def first_sentence(text, limit=150):
    """Первое предложение назначения без разметки ссылок (для компактного каталога)."""
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", (text or "").replace("\n", " ")).strip()
    m = re.match(r"(.{25,%d}?[.;])(\s|$)" % limit, t)
    return m.group(1) if m else (t[:limit].rstrip() + ("…" if len(t) > limit else ""))


def goal_short(reg, ids):
    short = {g["id"]: g.get("short", g["name"]) for g in reg["goals"]}
    return ", ".join(short[i] for i in ids if i in short) or "—"


def render_blocks(reg):
    """Сформированные участки README. Всё, что вне маркеров ECOSYSTEM:BEGIN/END, — текст человека."""
    projects = by_id(reg)
    types = {t["id"]: t["name"] for t in reg["types"]}
    out = {}
    L = ["| Проект | Тип | Для чего (коротко) | Чему служит |", "|---|---|---|---|"]
    for g in reg["groups"]:
        for pid in g["projects"]:
            p = projects[pid]
            title = "[%s](%s)" % (p["name"], readme_url(p)) if p.get("repo") and not p.get("title_only") else p["name"]
            if p["visibility"] == "private":
                title += " — приватный"
            L.append("| %s ([карточка](ecosystem-catalog.md#p-%s)) | %s | %s | %s |" % (
                title, pid, types[p["type"]], md_cell(first_sentence(p["purpose"]) or "—"), md_cell(goal_short(reg, p["serves"]))))
    out["overview"] = "\n".join(L) + "\n"
    L = ["| Вопрос | Куда идти | Маршрут Atlas |", "|---|---|---|"]
    for r in reg["routes"]:
        count = {}
        for a in r["answers"]:
            count[a["id"]] = count.get(a["id"], 0) + 1
        ans = "; ".join("[%s](%s) — %s" % (projects[a["id"]]["name"] + (" · " + short_doc(a["doc"]) if count[a["id"]] > 1 else ""), a["doc"], a["why"])
                        for a in r["answers"])
        L.append("| %s | %s | %s |" % (md_cell(r["question"]), md_cell(ans), md_cell(r.get("atlas_route") or "—")))
    out["routes"] = "\n".join(L) + "\n"
    L = []
    for g in reg["groups"]:
        L += ["### %s" % g["name"], ""]
        if g.get("description"):
            L += [g["description"], ""]
        L += ["| Проект | Тип | Что это и для чего нужен | Чему служит | Документы |", "|---|---|---|---|---|"]
        for pid in g["projects"]:
            p = projects[pid]
            title = p["name"]
            if p.get("repo"):
                title = "[%s](%s)" % (p["name"], readme_url(p))
            if p["visibility"] == "private":
                title += " — приватный"
            docs = []
            if p.get("entry_doc"):
                docs.append("[%s](%s)" % (short_doc(p["entry_doc"]), p["entry_doc"]))
            docs.append("[карточка](ecosystem-catalog.md#p-%s)" % pid)
            L.append("| %s | %s | %s | %s | %s |" % (title, types[p["type"]], md_cell(p["purpose"] or "—"),
                                                    md_cell(goal_short(reg, p["serves"])), " · ".join(docs)))
        L.append("")
    out["projects"] = "\n".join(L)
    L = render_diagram(reg) + ["", "Уровни связи:", ""]
    for lv in reg["levels"]:
        L.append("- **%s** — %s" % (lv["name"], lv["meaning"]))
    level_names = {l["id"]: l["name"] for l in reg["levels"]}
    order = {l["id"]: i for i, l in enumerate(reg["levels"])}
    strong = [r for r in reg["relations"] if r["level"] != "conceptual"]
    concept = len(reg["relations"]) - len(strong)
    L += ["", "| От | К | Уровень | Основание |", "|---|---|---|---|"]
    for r in sorted(strong, key=lambda r: (order[r["level"]], r["from"], r["to"])):
        L.append("| %s | %s | %s | %s ([источник](%s)) |" % (projects[r["from"]]["name"], projects[r["to"]]["name"],
                                                             level_names[r["level"]], md_cell(r["basis"]), r["source"]))
    if not strong:
        L.append("| — | — | — | связи выше концептуального уровня %s |" % NOT_CONFIRMED)
    L += ["", "Концептуальных связей (границы ответственности и общие идеи без плана и интерфейса): %d. "
          "Они вынесены в отдельный файл [ecosystem-relations.md](ecosystem-relations.md), где отделены от планов и реализации, и перечислены в карточках." % concept]
    out["relations"] = "\n".join(L) + "\n"
    credits = reg["meta"].get("credits", [])
    L = ["| Проект | Источник заимствования | Что известно о лицензии и происхождении | Где записано |", "|---|---|---|---|"]
    for c in credits:
        L.append("| %s | %s | %s | %s |" % (projects[c["project"]]["name"], md_cell(c["source"]), md_cell(c["note"]), md_cell(c.get("evidence", ""))))
    ex = reg["meta"].get("excluded_third_party", [])
    if ex:
        L += ["", "Сторонние репозитории, исключённые из активной карты и мониторинга (не удалены; сведения об авторстве остаются в самих репозиториях):", ""]
        L += ["- [%s](%s) — %s" % (e["name"], e["url"], e["note"]) for e in ex]
    out["credits"] = "\n".join(L) + "\n"
    out["sources"] = "\n".join("- [%s](%s) — %s%s" % (s["label"], s["url"], s["role"], (" (%s)" % s["access"]) if s.get("access") else "")
                               for s in reg["sources"]) + "\n"
    return out


def apply_blocks(text, blocks):
    """Подставляет блоки между маркерами; возвращает (новый текст, список проблем)."""
    problems, found = [], set()

    def sub(m):
        name = m.group(2)
        found.add(name)
        if name not in blocks:
            problems.append("неизвестный блок '%s'" % name)
            return m.group(0)
        return m.group(1) + blocks[name] + m.group(4)

    new = BLOCK.sub(sub, text)
    for name in BLOCK_NAMES:
        if name not in found:
            problems.append("в README нет блока ECOSYSTEM:BEGIN/END %s" % name)
    return new, problems


def render_diagram(reg):
    projects = by_id(reg)
    shown = [r for r in reg["relations"] if r["level"] in ("planned", "interface", "verified")]
    out = []
    if not shown:
        return ["_Планируемые, реализованные и проверенные связи %s._" % NOT_CONFIRMED]
    nodes = []
    for r in shown:
        for end in (r["from"], r["to"]):
            if end not in nodes:
                nodes.append(end)
    idx = {pid: "n%d" % i for i, pid in enumerate(nodes)}
    arrow = {"verified": "==>", "interface": "-->", "planned": "-.->"}
    out.append("```mermaid")
    out.append("flowchart LR")
    for pid in nodes:
        out.append('  %s["%s"]' % (idx[pid], projects[pid]["name"].replace('"', "'")))
    for r in sorted(shown, key=lambda r: (r["from"], r["to"], r["level"])):
        out.append("  %s %s %s" % (idx[r["from"]], arrow[r["level"]], idx[r["to"]]))
    out.append("```")
    out.append("")
    count = lambda lv: sum(1 for r in shown if r["level"] == lv)
    say = lambda n: ("в реестре: %d" % n) if n else NOT_CONFIRMED
    out.append("Толстая линия — проверенное совместное выполнение (%s); сплошная — реализованный интерфейс (%s); пунктир — запланированная интеграция (%s). "
               "Это не доказательство отсутствия таких связей во всей экосистеме. Концептуальные связи на схеме не показаны: они в отдельном файле [ecosystem-relations.md](ecosystem-relations.md) и в карточках." % (say(count("verified")), say(count("interface")), say(count("planned"))))
    return out


def render_catalog(reg):
    projects = by_id(reg)
    levels = {l["id"]: l["name"] for l in reg["levels"]}
    types = {t["id"]: t["name"] for t in reg["types"]}
    L = []
    L.append("# Карточки проектов Velantrim")
    L.append("")
    L.append("<!-- GENERATED: источник — projects/ecosystem.json. Не правьте вручную. -->")
    L.append("")
    L.append("> Сформировано из реестра [`ecosystem.json`](ecosystem.json); краткий вход — [`README.md`](README.md). "
             "Подробные статусы остаются в самих проектах: здесь только назначение, существенные ограничения и ссылки на первоисточники.")
    kinds = {"doc-only": "заявлено в документации", "report": "отчёт проекта", "manifest": "манифест", "code": "код", "test": "тест", "doc": "документ", "run": "запись запуска"}
    for g in reg["groups"]:
        for pid in g["projects"]:
            p = projects[pid]
            L.append("")
            L.append('<a id="p-%s"></a>' % pid)
            L.append("## %s" % p["name"])
            L.append("")
            facts = []
            if p.get("repo"):
                facts.append("репозиторий: [%s](%s)" % (p["repo"], repo_url(p)))
            facts.append("видимость: %s" % ("приватный" if p["visibility"] == "private" else "публичный"))
            facts.append("тип: %s" % types[p["type"]])
            L.append("; ".join(facts))
            if p.get("type_note"):
                L.append("")
                L.append("Тип — %s" % p["type_note"])
            L.append("")
            L.append("**Назначение.** %s" % (p["purpose"] or "название без описания (по решению владельца)"))
            if p.get("why_exists"):
                L.append("")
                L.append("**Зачем существует.** %s" % p["why_exists"])
            if p.get("role_in_concept"):
                L.append("")
                L.append("**Роль в замысле.** %s" % p["role_in_concept"])
            if p["serves"]:
                L.append("")
                L.append("**Обслуживаемые цели.** %s. %s" % (goal_names(reg, p["serves"]),
                                                          p.get("serves_note", "")))
            if p["confirmed"]:
                L.append("")
                L.append("**Подтверждено** (одно основание не подменяет другое: механизм в коде не значит, что он включён или запускался; "
                         "существующий тест не значит, что он проходил; запись запуска относится к своей версии и условиям):")
                for kind, title in KIND_TITLES:
                    items = [c for c in p["confirmed"] if c["evidenceKind"] == kind]
                    if items:
                        L.append("")
                        L.append("*%s:*" % title)
                        for c in items:
                            L.append("- %s ([источник](%s))" % (c["text"], c["source"]))
            if p["planned"]:
                L.append("")
                L.append("**Задумано, но не подтверждено:**")
                for c in p["planned"]:
                    L.append("- %s ([%s](%s))" % (c["text"], kinds.get(c["evidenceKind"], c["evidenceKind"]), c["source"]))
            if p["limits"]:
                L.append("")
                L.append("**Ограничения.** %s" % p["limits"])
            out_rel = [r for r in reg["relations"] if r["from"] == pid]
            in_rel = [r for r in reg["relations"] if r["to"] == pid]
            if out_rel or in_rel:
                L.append("")
                L.append("**Связи:**")
                for r in sorted(out_rel, key=lambda r: (r["to"], r["level"])):
                    L.append("- → [%s](#p-%s): %s — %s ([источник](%s))" % (
                        projects[r["to"]]["name"], r["to"], levels[r["level"]], r["basis"], r["source"]))
                for r in sorted(in_rel, key=lambda r: (r["from"], r["level"])):
                    L.append("- ← [%s](#p-%s): %s — %s ([источник](%s))" % (
                        projects[r["from"]]["name"], r["from"], levels[r["level"]], r["basis"], r["source"]))
            docs = []
            if p.get("entry_doc"):
                docs.append("вход: [%s](%s)" % (short_doc(p["entry_doc"]), p["entry_doc"]))
            if p.get("status_doc"):
                docs.append("статус проекта: [%s](%s)" % (short_doc(p["status_doc"]), p["status_doc"]))
            if docs:
                L.append("")
                L.append("**Документы.** " + "; ".join(docs))
            if p["history"]:
                L.append("")
                L.append("**История и основания:** " + "; ".join("[%s](%s)" % (h["label"], h["url"]) for h in p["history"]))
            if p.get("branches_note"):
                L.append("")
                L.append("**Где лежат результаты.** %s" % p["branches_note"])
            c = p["checked"]
            L.append("")
            if p["visibility"] == "private":
                L.append("**Проверка.** Приватный репозиторий: сведения только из публичных источников; автоматически не проверяется (не проверено).")
            else:
                basis = ", ".join("`%s`" % b for b in c.get("basis", []))
                auto = ", ".join("`%s`" % w for w in p["watch"]["purpose"] + p["watch"]["status"]) or "—"
                L.append("**Проверка.** Карточка сверена %s по `%s`%s. Автоматически наблюдаются: %s." % (
                    c["date"], c.get("ref", ""), (" (прочитано: %s)" % basis) if basis else "", auto))
            if p.get("unknowns"):
                L.append("")
                L.append("**Не установлено:** " + "; ".join(p["unknowns"]))
    return "\n".join(L).rstrip() + "\n"


def render_relations(reg):
    """Отдельный файл со всеми связями: уровни явно разделены, концептуальные не выдаются за планы и реализацию."""
    projects = by_id(reg)
    L = ["# Связи между проектами Velantrim", "",
         "<!-- GENERATED: источник — projects/ecosystem.json. Не правьте вручную. -->", "",
         "> Сформировано из реестра [`ecosystem.json`](ecosystem.json). Вход в карту — [`README.md`](README.md). "
         "Уровни не взаимозаменяемы: концептуальная связь — не план, план — не реализация, реализация — не проверенный запуск. "
         "Пустой уровень означает «%s», а не доказанное отсутствие связей во всей экосистеме." % NOT_CONFIRMED, ""]
    for lv in reg["levels"]:
        rows = sorted([r for r in reg["relations"] if r["level"] == lv["id"]], key=lambda r: (r["from"], r["to"], r["kind"]))
        L += ["## %s" % lv["name"], "", lv["meaning"][0].upper() + lv["meaning"][1:], ""]
        if not rows:
            L += ["_Связи этого уровня %s._" % NOT_CONFIRMED, ""]
            continue
        L += ["Связей: %d." % len(rows), "", "| От | К | Тип | Основание | Источник |", "|---|---|---|---|---|"]
        for r in rows:
            L.append("| %s | %s | %s | %s | [источник](%s) |" % (projects[r["from"]]["name"], projects[r["to"]]["name"], r["kind"], md_cell(r["basis"]), r["source"]))
        L.append("")
    return "\n".join(L).rstrip() + "\n"


# ---------------------------------------------------------------- транспорты

class ApiTransport:
    """GitHub REST API по HTTPS (в Actions — с встроенным GITHUB_TOKEN)."""

    def __init__(self, token=None):
        self.token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    def _get(self, path):
        req = urllib.request.Request("https://api.github.com" + path, headers={
            "Accept": "application/vnd.github+json", "User-Agent": "velantrim-ecosystem-check",
            "X-GitHub-Api-Version": "2022-11-28"})
        if self.token:
            req.add_header("Authorization", "Bearer " + self.token)
        last = None
        for _ in range(2):
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    return {"status": "ok", "json": json.load(r)}
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return {"status": "missing"}
                if e.code in (403, 429):
                    if e.headers.get("x-ratelimit-remaining") == "0" or e.code == 429:
                        return {"status": "rate-limited", "detail": "лимит запросов API"}
                    return {"status": "forbidden", "detail": "HTTP %d" % e.code}
                last = {"status": "error", "detail": "HTTP %d" % e.code}
                if e.code < 500:
                    return last
            except Exception as e:  # сеть, таймаут
                last = {"status": "error", "detail": type(e).__name__}
        return last

    def repo_meta(self, repo):
        r = self._get("/repos/" + repo)
        return _meta_from(r)

    def file(self, repo, ref, path):
        r = self._get("/repos/%s/contents/%s?ref=%s" % (repo, path, ref))
        if r["status"] != "ok":
            return r
        j = r["json"]
        if isinstance(j, list) or j.get("type") != "file":
            return {"status": "missing"}
        text = None
        if j.get("encoding") == "base64" and j.get("content"):
            text = base64.b64decode(j["content"]).decode("utf-8", "replace")
        else:
            b = self._get("/repos/%s/git/blobs/%s" % (repo, j["sha"]))
            if b["status"] == "ok" and b["json"].get("encoding") == "base64":
                text = base64.b64decode(b["json"]["content"]).decode("utf-8", "replace")
        return {"status": "ok", "blob": j["sha"], "text": text}

    def blob_text(self, repo, sha):
        b = self._get("/repos/%s/git/blobs/%s" % (repo, sha))
        if b["status"] == "ok" and b["json"].get("encoding") == "base64":
            return base64.b64decode(b["json"]["content"]).decode("utf-8", "replace")
        return None


class GhTransport(ApiTransport):
    """То же через gh CLI (удобно локально, где уже есть вход в gh)."""

    def _get(self, path):
        p = subprocess.run(["gh", "api", "-H", "Accept: application/vnd.github+json", path.lstrip("/")],
                           capture_output=True, text=True)
        if p.returncode == 0:
            try:
                return {"status": "ok", "json": json.loads(p.stdout)}
            except ValueError:
                return {"status": "error", "detail": "не JSON"}
        err = (p.stderr + p.stdout).lower()
        if "404" in err:
            return {"status": "missing"}
        if "rate limit" in err:
            return {"status": "rate-limited", "detail": "лимит запросов API"}
        if "403" in err:
            return {"status": "forbidden", "detail": "HTTP 403"}
        return {"status": "error", "detail": "gh api"}


class LocalTransport:
    """Локальные клоны вместо сети: для тестов и офлайн-инициализации baseline.

    mapping: {"owner/name": "/путь/к/клону"}; meta — необязательный словарь
    {"owner/name": {full_name, private, archived, default_branch, description}}.
    Если meta не задан, archived и description записываются как null (неизвестно).
    """

    def __init__(self, mapping, meta=None):
        self.mapping = mapping
        self.meta = meta or {}

    def repo_meta(self, repo):
        if repo not in self.mapping:
            return {"status": "missing"}
        m = self.meta.get(repo)
        if m is None:
            return {"status": "ok", "full_name": repo, "private": False, "archived": None,
                    "default_branch": "main", "description": None}
        if m.get("status") and m["status"] != "ok":
            return m
        return dict({"status": "ok"}, **m)

    def file(self, repo, ref, path):
        base = self.mapping.get(repo)
        if not base:
            return {"status": "missing"}
        f = Path(base) / path
        if not f.is_file():
            return {"status": "missing"}
        data = f.read_bytes()
        blob = hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
        return {"status": "ok", "blob": blob, "text": data.decode("utf-8", "replace")}

    def blob_text(self, repo, sha):
        base = self.mapping.get(repo)
        if not base:
            return None
        p = subprocess.run(["git", "-C", base, "cat-file", "-p", sha], capture_output=True)
        return p.stdout.decode("utf-8", "replace") if p.returncode == 0 else None


def _meta_from(r):
    if r["status"] != "ok":
        return r
    j = r["json"]
    return {"status": "ok", "full_name": j.get("full_name"), "private": bool(j.get("private")),
            "archived": bool(j.get("archived")), "default_branch": j.get("default_branch"),
            "description": j.get("description")}


def make_transport(args):
    if args.transport == "local":
        if not args.local_map:
            raise ValueError("для --transport local нужен --local-map")
        mapping = load_json(args.local_map)
        meta = load_json(args.local_meta) if args.local_meta else None
        return LocalTransport(mapping, meta)
    if args.transport == "gh":
        return GhTransport()
    return ApiTransport()


# ---------------------------------------------------------------- check

def watched_paths(p):
    seen, out = set(), []
    for kind in ("purpose", "status"):
        for path in p["watch"].get(kind, []):
            if path not in seen:
                seen.add(path)
                out.append((kind, path))
    return out


def observe(reg, tr, only=None):
    """Собирает наблюдаемое состояние публичных проектов. Приватные не трогаем."""
    obs, skipped = {}, []
    for p in reg["projects"]:
        if only and p["id"] not in only:
            continue
        if not p.get("repo"):
            continue
        if p["visibility"] != "public":
            skipped.append((p, "приватный репозиторий: доступ не используется"))
            continue
        meta = tr.repo_meta(p["repo"])
        entry = {"meta": meta, "files": {}}
        if meta["status"] == "ok" and not meta.get("private"):
            ref = meta.get("default_branch") or "main"
            for kind, path in watched_paths(p):
                entry["files"][path] = dict(tr.file(p["repo"], ref, path), kind=kind)
        obs[p["id"]] = entry
    return obs, skipped


def compare(reg, base, obs, skipped, tr):
    """Классифицирует расхождения. Реестр и baseline не меняются."""
    projects = by_id(reg)
    res = {"review": [], "technical": [], "not_checked": [], "gaps": [], "ok": []}
    for p, why in skipped:
        res["not_checked"].append((p["id"], why))
    for pid, o in obs.items():
        p = projects[pid]
        b = base.get("projects", {}).get(pid)
        meta = o["meta"]
        if meta["status"] == "missing":
            res["review"].append({"id": pid, "kind": "доступность", "what": "репозиторий %s не найден (удалён, переименован без перенаправления или стал приватным)" % p["repo"],
                                  "fields": ["repo", "visibility"], "level": "назначение"})
            continue
        if meta["status"] != "ok":
            res["not_checked"].append((pid, "не проверено: %s" % meta.get("detail", meta["status"])))
            continue
        bm = (b or {}).get("meta")
        if not b or bm is None:
            res["gaps"].append((pid, "нет базовой отметки метаданных"))
        else:
            pairs = [("full_name", "имя репозитория", "repo"), ("private", "видимость", "visibility"),
                     ("archived", "архивирование", "type"), ("description", "описание на GitHub", "purpose"),
                     ("default_branch", "основная ветка", "entry_doc")]
            for key, label, field in pairs:
                was, now = bm.get(key), meta.get(key)
                if was is None:
                    res["gaps"].append((pid, "метаданные: «%s» не зафиксировано" % label))
                elif was != now:
                    res["review"].append({"id": pid, "kind": label, "what": "было %r → стало %r" % (was, now),
                                          "fields": [field], "level": "назначение"})
        if meta.get("private"):
            res["review"].append({"id": pid, "kind": "видимость", "what": "репозиторий стал приватным: содержимое больше не читается",
                                  "fields": ["visibility"], "level": "назначение"})
            continue
        changed_here = False
        for path, f in o["files"].items():
            bf = ((b or {}).get("files") or {}).get(path)
            if f["status"] == "missing":
                res["review"].append({"id": pid, "kind": "наблюдаемый файл", "what": "файл %s отсутствует" % path,
                                      "fields": ["watch", "entry_doc", "status_doc"], "level": "назначение"})
                changed_here = True
                continue
            if f["status"] != "ok":
                res["not_checked"].append((pid, "файл %s не проверен: %s" % (path, f.get("detail", f["status"]))))
                continue
            if bf is None:
                res["gaps"].append((pid, "файл %s: нет базовой отметки" % path))
                continue
            if f["blob"] == bf["blob"]:
                continue
            new_norm = sha256(norm_text(f["text"] or ""))
            if new_norm == bf.get("norm"):
                res["technical"].append({"id": pid, "path": path, "what": "изменилось только форматирование (пробелы/переводы строк)"})
                continue
            old = tr.blob_text(p["repo"], bf["blob"])
            diff = None
            if old is not None and f["text"] is not None:
                diff = list(difflib.unified_diff(old.splitlines(), f["text"].splitlines(), "было", "стало", lineterm="", n=2))
            kind = "документ о назначении" if f["kind"] == "purpose" else "явный статус или интерфейс"
            fields = ["purpose", "confirmed", "limits"] if f["kind"] == "purpose" else ["confirmed", "planned", "limits"]
            res["review"].append({"id": pid, "kind": kind, "what": "изменился %s" % path, "path": path, "diff": diff,
                                  "fields": fields, "level": "назначение" if f["kind"] == "purpose" else "статус",
                                  "url": "%s/blob/%s/%s" % (repo_url(p), meta.get("default_branch") or "main", path)})
            changed_here = True
        if not changed_here and not any(i["id"] == pid for i in res["review"]):
            res["ok"].append(pid)
    return res


def cross_check(reg, tr):
    """Согласованность с Atlas и с индексом ecosystem-evidence (только чтение)."""
    notes = []
    pj = tr.file("velantrian/Velantrim-Atlas-App", "main", "atlas/projects.json")
    if pj["status"] == "ok" and pj.get("text"):
        try:
            atlas_ids = {x["id"] for x in json.loads(pj["text"])["projects"]}
            mapped = {p["cross"]["atlas"] for p in reg["projects"] if p.get("cross", {}).get("atlas")}
            mapped |= set(reg["meta"].get("atlas_areas", {}))  # известные области без репозитория: см. meta.atlas_areas
            for p in reg["projects"]:
                a = p.get("cross", {}).get("atlas")
                if a and a not in atlas_ids:
                    notes.append(("review", "Atlas: проект «%s» ссылается на id «%s», которого нет в atlas/projects.json" % (p["name"], a)))
            for aid in sorted(atlas_ids - mapped):
                notes.append(("info", "Atlas перечисляет «%s», но в реестре нет соответствующей записи (проект или область: см. meta.atlas_areas)" % aid))
            sj = tr.file("velantrian/Velantrim-Atlas-App", "main", "atlas/sources.json")
            if sj["status"] == "ok" and sj.get("text"):
                exact = {p["repo"] for p in reg["projects"] if p.get("repo")}
                lower = {r.lower(): r for r in exact}
                for src in json.loads(sj["text"])["sources"]:
                    m = GH_URL.match(src.get("url", ""))
                    if m and m.group(1) == OWNER:
                        full = "%s/%s" % (m.group(1), m.group(2))
                        real = lower.get(full.lower())
                        if real and real != full:
                            notes.append(("info", "Atlas sources.json: «%s» записан как %s, точное имя — %s" % (src["id"], full, real)))
        except (ValueError, KeyError, TypeError):
            notes.append(("info", "Atlas: atlas/projects.json не удалось разобрать"))
    else:
        notes.append(("info", "Atlas: не проверено (%s)" % pj.get("detail", pj["status"])))
    ix = tr.file("velantrian/velantrim", "main", "tools/ecosystem-evidence/ecosystem_status_index.json")
    if ix["status"] == "ok" and ix.get("text"):
        try:
            repos = {p["repo"] for p in reg["projects"] if p.get("repo")}
            ids = {p["cross"]["evidence_index"] for p in reg["projects"] if p.get("cross", {}).get("evidence_index")}
            for item in json.loads(ix["text"])["projects"]:
                if item.get("repo") and item["repo"] not in repos:
                    notes.append(("review", "Индекс evidence: репозиторий «%s» не совпадает по точному имени ни с одной записью реестра" % item["repo"]))
                elif item["id"] not in ids and item.get("repo") in repos:
                    notes.append(("info", "Индекс evidence: id «%s» не указан в cross.evidence_index соответствующей записи" % item["id"]))
        except (ValueError, KeyError, TypeError):
            notes.append(("info", "Индекс evidence: не удалось разобрать"))
    else:
        notes.append(("info", "Индекс evidence: не проверено (%s)" % ix.get("detail", ix["status"])))
    return notes


def build_report(reg, res, notes, today, cov=None):
    review = list(res["review"])
    review_notes = [t for k, t in notes if k == "review"]
    n_review = len(review) + len(review_notes)
    L = ["# Ecosystem check — %s" % today, ""]
    if n_review:
        L.append("**Результат: ТРЕБУЕТ РАССМОТРЕНИЯ — %d.** Реестр и baseline автоматически не менялись." % n_review)
    else:
        L.append("**Результат: NO CHANGE** — только в проверенных источниках.")
    if cov:
        L.append("")
        L.append("**Охват:** проверено %d из %d проектов с репозиторием; не проверено (приватные, недоступные, лимит): %d; "
                 "источников без базовой отметки: %d. NO CHANGE не означает полного охвата: непроверенные и не имеющие базовой отметки источники "
                 "в результат не входят." % cov)
    L += ["", "Проверяются: переименование, архивирование, видимость и описание репозитория, документы о назначении и явный статус. "
          "Коммиты, не затрагивающие эти источники, не отслеживаются. Статус реализации автоматически не повышается: "
          "новое описание — повод проверить карточку, а не доказательство.", ""]
    if review or review_notes:
        L += ["## Требует рассмотрения", ""]
        for it in review:
            L.append("### %s — %s" % (by_id(reg)[it["id"]]["name"], it["kind"]))
            L.append("- Что изменилось: %s" % it["what"])
            L.append("- Характер изменения: %s" % it["level"])
            L.append("- Какие поля карточки сверить: %s" % ", ".join("`%s`" % f for f in it["fields"]))
            if it.get("url"):
                L.append("- Источник: %s" % it["url"])
            if it.get("diff"):
                L.append("")
                L.append("```diff")
                for line in it["diff"][:DIFF_LINES]:
                    L.append(line.replace("```", "'''"))
                if len(it["diff"]) > DIFF_LINES:
                    L.append("… (ещё %d строк)" % (len(it["diff"]) - DIFF_LINES))
                L.append("```")
            elif "path" in it:
                L.append("- Прежняя версия недоступна для сравнения.")
            L.append("")
        for t in review_notes:
            L.append("- " + t)
        L.append("")
    if res["technical"]:
        L += ["## Технические изменения (решения не требуют)", ""]
        for t in res["technical"]:
            L.append("- %s: `%s` — %s" % (by_id(reg)[t["id"]]["name"], t["path"], t["what"]))
        L.append("")
    if res["not_checked"]:
        L += ["## Не проверено", ""]
        for pid, why in res["not_checked"]:
            L.append("- %s — %s" % (by_id(reg)[pid]["name"], why))
        L.append("")
    if res["gaps"]:
        L += ["## Нет базовой отметки", "",
              "Для этих источников baseline не содержит значения; они не считаются изменением. Предлагаемый baseline сохраняется "
              "в артефакте `proposed-baseline.json` (если запущено с --propose); применять его нужно отдельным согласованным изменением.", ""]
        for pid, why in res["gaps"]:
            L.append("- %s — %s" % (by_id(reg)[pid]["name"], why))
        L.append("")
    info = [t for k, t in notes if k == "info"]
    if info:
        L += ["## Согласованность с соседними реестрами (справочно)", ""]
        L += ["- " + t for t in info]
        L.append("")
    return "\n".join(L).rstrip() + "\n", n_review


def proposed_baseline(reg, obs, old, today):
    new = {"schema_version": "1", "recorded": today, "note": old.get("note", ""), "projects": {}}
    for pid, o in obs.items():
        prev = old.get("projects", {}).get(pid)
        if o["meta"]["status"] != "ok":
            continue  # не удалось прочитать: прежняя запись сохранится ниже
        m = o["meta"]
        entry = {"repo": by_id(reg)[pid]["repo"],
                 "meta": {k: m.get(k) for k in ("full_name", "private", "archived", "default_branch", "description")},
                 "files": {}}
        for path, f in o["files"].items():
            if f["status"] == "ok":
                entry["files"][path] = {"blob": f["blob"], "norm": sha256(norm_text(f["text"] or ""))}
            elif prev and path in (prev.get("files") or {}):
                entry["files"][path] = prev["files"][path]
        new["projects"][pid] = entry
    for pid, prev in old.get("projects", {}).items():
        new["projects"].setdefault(pid, prev)
    new["projects"] = {k: new["projects"][k] for k in sorted(new["projects"])}
    return new


# ---------------------------------------------------------------- команды

def cmd_validate(args):
    reg = load_json(args.registry)
    errs = validate(reg)
    for e in errs:
        print("ОШИБКА:", safe_line(e))
    print("validate: %s (проектов: %d, связей: %d)" % ("ЕСТЬ ПРОБЛЕМЫ: %d" % len(errs) if errs else "OK",
                                                      len(reg.get("projects", [])), len(reg.get("relations", []))))
    return EXIT_PROBLEM if errs else EXIT_OK


def cmd_render(args):
    reg = load_json(args.registry)
    errs = validate(reg)
    if errs:
        for e in errs:
            print("ОШИБКА:", safe_line(e))
        return EXIT_PROBLEM
    readme, catalog, relations = Path(args.readme_out), Path(args.catalog_out), Path(args.relations_out)
    if not readme.exists():
        print("ОШИБКА: нет %s — README с маркерами ECOSYSTEM:BEGIN/END создаётся человеком, render заполняет только блоки" % readme.name)
        return EXIT_PROBLEM
    old_readme = readme.read_text(encoding="utf-8")
    new_readme, problems = apply_blocks(old_readme, render_blocks(reg))
    if problems:
        for e in problems:
            print("ОШИБКА:", e)
        return EXIT_PROBLEM
    outputs = {readme: (old_readme, new_readme),
               catalog: (catalog.read_text(encoding="utf-8") if catalog.exists() else None, render_catalog(reg)),
               relations: (relations.read_text(encoding="utf-8") if relations.exists() else None, render_relations(reg))}
    bad = 0
    for path, (current, text) in outputs.items():
        if args.check:
            if current != text:
                print("УСТАРЕЛО: %s не совпадает с реестром — выполните render" % path.name)
                bad += 1
        elif current != text:
            path.write_text(text, encoding="utf-8", newline="\n")
            print("записано:", path.name)
        else:
            print("без изменений:", path.name)
    if args.check:
        print("render --check: %s" % ("РАСХОЖДЕНИЕ" if bad else "OK"))
    return EXIT_PROBLEM if bad else EXIT_OK


def _only(args):
    return set(args.only.split(",")) if args.only else None


def cmd_check(args):
    reg = load_json(args.registry)
    errs = validate(reg)
    if errs:
        for e in errs:
            print("ОШИБКА:", safe_line(e))
        return EXIT_ERROR
    base = load_json(args.baseline) if Path(args.baseline).exists() else {"projects": {}}
    tr = make_transport(args)
    obs, skipped = observe(reg, tr, _only(args))
    res = compare(reg, base, obs, skipped, tr)
    notes = cross_check(reg, tr) if not args.no_cross else []
    today = args.today or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    total = len([p for p in reg["projects"] if p.get("repo")])
    checked = len([pid for pid, o in obs.items() if o["meta"]["status"] == "ok"])
    cov = (checked, total, len(res["not_checked"]), len(res["gaps"]))
    text, n_review = build_report(reg, res, notes, today, cov)
    if args.summary:
        with open(args.summary, "a", encoding="utf-8") as f:
            f.write(text)
    if args.json:
        dump_json(args.json, {"date": today, "review": n_review, "not_checked": len(res["not_checked"]),
                              "gaps": len(res["gaps"]), "technical": len(res["technical"]),
                              "review_items": [{k: v for k, v in it.items() if k != "diff"} for it in res["review"]]})
    if args.propose:
        dump_json(args.propose, proposed_baseline(reg, obs, base, today))
    # в stdout — только управляемые строки, без текста из чужих репозиториев
    print("check: %s; на рассмотрение: %d; технических: %d; охват: %d из %d проектов; не проверено: %d; без базовой отметки: %d%s" % (
        "ТРЕБУЕТ РАССМОТРЕНИЯ" if n_review else "NO CHANGE (только в проверенных источниках)", n_review, len(res["technical"]),
        checked, total, len(res["not_checked"]), len(res["gaps"]), "" if n_review else "; это не полный охват"))
    if not args.summary:
        print(text if not any(l.startswith("::") for l in text.splitlines()) else "\n".join(safe_line(l) for l in text.splitlines()))
    return EXIT_REVIEW if n_review else EXIT_OK


def cmd_baseline(args):
    reg = load_json(args.registry)
    errs = validate(reg)
    if errs:
        for e in errs:
            print("ОШИБКА:", safe_line(e))
        return EXIT_ERROR
    old = load_json(args.baseline) if Path(args.baseline).exists() else {"projects": {}, "note": ""}
    tr = make_transport(args)
    obs, _ = observe(reg, tr, _only(args))
    today = args.today or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    new = proposed_baseline(reg, obs, old, today)
    if not old.get("note"):
        new["note"] = ("Отпечатки наблюдаемых источников (git blob SHA и хэш нормализованного текста) и метаданные репозиториев. "
                       "Это не каталог: данные о проектах — в ecosystem.json. Обновляется только по явной команде baseline "
                       "после рассмотрения изменений. null в метаданных = не зафиксировано.")
    dump_json(args.baseline, new)
    print("baseline: записано проектов: %d" % len(new["projects"]))
    return EXIT_OK


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["validate", "render", "check", "baseline"])
    ap.add_argument("--registry", default=str(REGISTRY))
    ap.add_argument("--baseline", default=str(BASELINE))
    ap.add_argument("--readme-out", default=str(README_OUT))
    ap.add_argument("--catalog-out", default=str(CATALOG_OUT))
    ap.add_argument("--relations-out", default=str(RELATIONS_OUT))
    ap.add_argument("--check", action="store_true", help="render: только сравнить с файлами")
    ap.add_argument("--transport", choices=["api", "gh", "local"], default=os.environ.get("ECOSYSTEM_TRANSPORT", "api"))
    ap.add_argument("--local-map", help="local: JSON {'owner/name': '/путь'}")
    ap.add_argument("--local-meta", help="local: JSON с метаданными репозиториев")
    ap.add_argument("--only", help="id проектов через запятую")
    ap.add_argument("--summary", help="дописать отчёт Markdown в файл (например $GITHUB_STEP_SUMMARY)")
    ap.add_argument("--json", help="записать краткий JSON-отчёт")
    ap.add_argument("--propose", help="записать предлагаемый baseline (без применения)")
    ap.add_argument("--no-cross", action="store_true", help="не сверять с Atlas и индексом evidence")
    ap.add_argument("--today", help="дата отчёта YYYY-MM-DD (для тестов)")
    args = ap.parse_args(argv)
    try:
        return {"validate": cmd_validate, "render": cmd_render, "check": cmd_check, "baseline": cmd_baseline}[args.command](args)
    except (OSError, ValueError, KeyError) as e:
        print("ОШИБКА ЗАПУСКА: %s: %s" % (type(e).__name__, safe_line(str(e))))
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
