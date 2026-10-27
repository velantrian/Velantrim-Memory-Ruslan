#!/usr/bin/env python3
"""Velantrim Ecosystem: реестр проектов, генерация представлений, проверка источников.

Единственный источник данных — projects/ecosystem.json. Всё остальное
(projects/README.md, projects/ecosystem-catalog.md) генерируется из него.

Команды:
  validate          проверить схему реестра, имена репозиториев, правила приватности
  render [--check]  сформировать представления (с --check только сравнить с файлами)

Только стандартная библиотека. Скрипт работает локально, ничего не публикует,
не обращается к сети, не использует LLM и не требует секретов.

Коды выхода: 0 — всё в порядке; 1 — validate или render --check нашёл проблему;
2 — ошибка запуска.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "projects" / "ecosystem.json"
README_OUT = ROOT / "projects" / "README.md"
CATALOG_OUT = ROOT / "projects" / "ecosystem-catalog.md"

EXIT_OK, EXIT_PROBLEM, EXIT_ERROR = 0, 1, 2
EVIDENCE_OK = {"doc", "code", "test", "run"}
# запись успешного запуска должна называть версию (коммит, тег, дата) и условия
RUN_HINT = re.compile(r"[0-9a-f]{7,40}|\d{4}-\d{2}-\d{2}|\bv\d|@|run_\d+|PR #\d+")
ATLAS_ROUTES = "https://github.com/velantrian/Velantrim-Atlas-App/blob/main/atlas/routes.json"
MASTER_MAP = "https://github.com/velantrian/velantrim/blob/main/docs/architecture/VELANTRIM_ECOSYSTEM_MASTER_MAP.md"
NOT_CONFIRMED = "не подтверждены в рамках этой проверки"
VISIBILITIES = {"public", "private"}
GH_URL = re.compile(r"https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)")
OWNER = "velantrian"


# ---------------------------------------------------------------- утилиты

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dump_json(path, data):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


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


def shown_repo(p):
    """Репозиторий для вывода: у записи title_only идентификатор не показывается никогда."""
    return "" if p.get("title_only") else p.get("repo", "")


def repo_url(p):
    return "https://github.com/" + shown_repo(p) if shown_repo(p) else ""


def readme_url(p):
    """Имя проекта в таблицах ведёт к README репозитория (как в прежнем справочнике)."""
    return repo_url(p) + "/blob/main/README.md" if shown_repo(p) else ""


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
        if p.get("title_only"):
            # запись «только название»: никаких идентификаторов или ссылок на репозиторий
            for key in ("repo", "entry_doc", "status_doc", "slug", "url", "repository"):
                if p.get(key):
                    errs.append("%s: у записи title_only не должно быть поля '%s' (только название)" % (pid, key))
            if any(GH_URL.search(s) or OWNER + "/" in s for s in walk_strings(p)):
                errs.append("%s: у записи title_only не должно быть идентификатора или ссылки на репозиторий" % pid)
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
            title = "[%s](%s)" % (p["name"], readme_url(p)) if shown_repo(p) else p["name"]
            if p["visibility"] == "private":
                title += " — приватный"
            L.append("| %s ([карточка](ecosystem-catalog.md#p-%s)) | %s | %s | %s |" % (
                title, pid, types[p["type"]], md_cell(first_sentence(p["purpose"]) or "—"), md_cell(goal_short(reg, p["serves"]))))
    out["overview"] = "\n".join(L) + "\n"
    L = ["Это примеры переходов к Atlas, а не отдельный маршрутизатор. Навигацию, полный набор маршрутов и правила выбора владельца ведёт [Atlas](%s); здесь они не повторяются." % ATLAS_ROUTES,
         "", "| Вопрос | Маршрут Atlas | Куда читать первоисточник |", "|---|---|---|"]
    for r in reg["routes"]:
        count = {}
        for a in r["answers"]:
            count[a["id"]] = count.get(a["id"], 0) + 1
        ans = "; ".join("[%s](%s) — %s" % (projects[a["id"]]["name"] + (" · " + short_doc(a["doc"]) if count[a["id"]] > 1 else ""), a["doc"], a["why"])
                        for a in r["answers"])
        L.append("| %s | %s | %s |" % (md_cell(r["question"]), md_cell(r["atlas_route"]), md_cell(ans)))
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
            if shown_repo(p):
                title = "[%s](%s)" % (p["name"], readme_url(p))
            if p["visibility"] == "private":
                title += " — приватный"
            docs = []
            if p.get("entry_doc") and not p.get("title_only"):
                docs.append("[%s](%s)" % (short_doc(p["entry_doc"]), p["entry_doc"]))
            docs.append("[карточка](ecosystem-catalog.md#p-%s)" % pid)
            L.append("| %s | %s | %s | %s | %s |" % (title, types[p["type"]], md_cell(p["purpose"] or "—"),
                                                    md_cell(goal_short(reg, p["serves"])), " · ".join(docs)))
        L.append("")
    out["projects"] = "\n".join(L)
    L = ["Уровни связи:", ""]
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
    L += ["", "Концептуальные связи (%d: границы ответственности и общие идеи без плана и интерфейса) здесь не повторяются: "
          "общая композиция описана в [Master Map](%s) (§3–4), связи конкретного проекта — в его карточке." % (concept, MASTER_MAP)]
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
            if shown_repo(p):
                facts.append("репозиторий: [%s](%s)" % (shown_repo(p), repo_url(p)))
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
            if p.get("entry_doc") and not p.get("title_only"):
                docs.append("вход: [%s](%s)" % (short_doc(p["entry_doc"]), p["entry_doc"]))
            if p.get("status_doc") and not p.get("title_only"):
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
                L.append("**Проверка.** Карточка сверена %s по `%s`%s. Файлы для следующей ручной сверки: %s." % (
                    c["date"], c.get("ref", ""), (" (прочитано: %s)" % basis) if basis else "", auto))
            if p.get("unknowns"):
                L.append("")
                L.append("**Не установлено:** " + "; ".join(p["unknowns"]))
    return "\n".join(L).rstrip() + "\n"


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
    readme, catalog = Path(args.readme_out), Path(args.catalog_out)
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
               catalog: (catalog.read_text(encoding="utf-8") if catalog.exists() else None, render_catalog(reg))}
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


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["validate", "render"])
    ap.add_argument("--registry", default=str(REGISTRY))
    ap.add_argument("--readme-out", default=str(README_OUT))
    ap.add_argument("--catalog-out", default=str(CATALOG_OUT))
    ap.add_argument("--check", action="store_true", help="render: только сравнить с файлами")
    args = ap.parse_args(argv)
    try:
        return {"validate": cmd_validate, "render": cmd_render}[args.command](args)
    except (OSError, ValueError, KeyError) as e:
        print("ОШИБКА ЗАПУСКА: %s: %s" % (type(e).__name__, safe_line(str(e))))
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
