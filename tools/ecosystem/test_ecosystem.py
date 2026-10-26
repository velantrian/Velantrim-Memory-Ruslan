"""Тесты tools/ecosystem/ecosystem.py на локальных фикстурах (без сети).

Запуск: python3 -m unittest discover -s tools/ecosystem -v
"""
import contextlib
import copy
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ecosystem as eco  # noqa: E402


def sample_registry():
    return {
        "schema_version": "1",
        "meta": {"updated": "2026-10-21", "external_repos": []},
        "goals": [{"id": "exocortex", "name": "Личный экзокортекс", "short": "экзокортекс", "source": "WORKBOARD.md"}],
        "levels": [{"id": "verified", "name": "Проверенный запуск", "meaning": "m"},
                   {"id": "interface", "name": "Интерфейс", "meaning": "m"},
                   {"id": "planned", "name": "План", "meaning": "m"},
                   {"id": "conceptual", "name": "Концепция", "meaning": "m"}],
        "types": [{"id": "component", "name": "Компонент"}, {"id": "docs", "name": "Документация"}],
        "sources": [{"id": "s", "label": "Доска", "url": "https://example.org/x", "role": "история", "access": "нужен вход"}],
        "routes": [{"question": "Где память?", "answers": [{"id": "alpha", "doc": "https://github.com/velantrian/Alpha/blob/main/README.md", "why": "потому"}], "atlas_route": ""}],
        "groups": [{"id": "g", "name": "Группа", "description": "", "projects": ["alpha", "beta", "secret"]}],
        "projects": [
            {"id": "alpha", "name": "Alpha", "repo": "velantrian/Alpha", "visibility": "public", "type": "component",
             "purpose": "Делает альфу.", "why_exists": "Чтобы была альфа.", "role_in_concept": "Часть памяти.", "serves": ["exocortex"], "confirmed": [{"text": "Умеет X", "source": "https://github.com/velantrian/Alpha/blob/main/x.py", "evidenceKind": "code"}, {"text": "Запуск 2026-10-26 на abc1234: прошёл.", "source": "https://github.com/velantrian/Alpha/blob/main/run.md", "evidenceKind": "run"}],
             "planned": [], "limits": "Не готово.", "entry_doc": "https://github.com/velantrian/Alpha/blob/main/README.md", "status_doc": "",
             "history": [], "watch": {"purpose": ["README.md"], "status": ["STATUS.md"]}, "checked": {"date": "2026-10-21", "ref": "main@abc1234", "basis": ["README.md"]},
             "cross": {"atlas": "alpha"}},
            {"id": "beta", "name": "Beta", "repo": "velantrian/Beta", "visibility": "public", "type": "docs",
             "purpose": "Документы беты.", "why_exists": "Для документов.", "role_in_concept": "Вспомогательная.", "serves": [], "confirmed": [], "planned": [], "limits": "", "entry_doc": "", "status_doc": "",
             "history": [], "watch": {"purpose": ["README.md"], "status": []}, "checked": {"date": "2026-10-21", "ref": "main@def5678", "basis": []}},
            {"id": "secret", "name": "Secret", "repo": "velantrian/Secret", "visibility": "private", "type": "docs",
             "purpose": "Приватное.", "why_exists": "Публично известное.", "role_in_concept": "Личная память.", "serves": [], "confirmed": [], "planned": [], "limits": "", "entry_doc": "", "status_doc": "",
             "history": [], "watch": {"purpose": [], "status": []}, "checked": {"date": "2026-10-21", "ref": "", "basis": []}},
        ],
        "relations": [{"from": "alpha", "to": "beta", "kind": "related", "level": "conceptual", "basis": "описано", "source": "https://github.com/velantrian/Alpha/blob/main/README.md"},
                      {"from": "beta", "to": "alpha", "kind": "depends-on", "level": "planned", "basis": "план", "source": "https://github.com/velantrian/Beta/blob/main/README.md"}],
    }


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = eco.main(argv)
    return code, out.getvalue()


def git(cwd, *a):
    subprocess.run(["git", "-C", str(cwd)] + list(a), check=True, capture_output=True)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = Path(self.tmp.name)
        self.reg_path = self.t / "ecosystem.json"
        self.base_path = self.t / "baseline.json"
        self.reg = sample_registry()
        eco.dump_json(self.reg_path, self.reg)
        self.clones = {}
        for name in ("Alpha", "Beta"):
            d = self.t / name
            d.mkdir()
            git(d, "init", "-q", "-b", "main") if False else subprocess.run(["git", "init", "-q", str(d)], check=True)
            git(d, "config", "user.email", "t@example.org")
            git(d, "config", "user.name", "t")
            (d / "README.md").write_text("# %s\n\nНазначение исходное.\n" % name, encoding="utf-8")
            (d / "STATUS.md").write_text("status: research\n", encoding="utf-8")
            git(d, "add", "-A")
            git(d, "commit", "-q", "-m", "init")
            self.clones["velantrian/" + name] = str(d)
        self.map_path = self.t / "map.json"
        eco.dump_json(self.map_path, self.clones)
        self.meta = {r: {"full_name": r, "private": False, "archived": False, "default_branch": "main", "description": "Описание"}
                     for r in self.clones}
        self.meta_path = self.t / "meta.json"
        eco.dump_json(self.meta_path, self.meta)
        # cross-check читает файлы Atlas/velantrim: в локальном режиме их нет, значит справочно «не проверено»

    def tearDown(self):
        self.tmp.cleanup()

    def argv(self, cmd, *extra):
        return [cmd, "--registry", str(self.reg_path), "--baseline", str(self.base_path), "--transport", "local",
                "--local-map", str(self.map_path), "--local-meta", str(self.meta_path), "--today", "2026-10-21"] + list(extra)

    def set_meta(self, repo, **kw):
        self.meta[repo].update(kw)
        eco.dump_json(self.meta_path, self.meta)

    def edit(self, name, fname, text, commit=True):
        d = Path(self.clones["velantrian/" + name])
        (d / fname).write_text(text, encoding="utf-8")
        if commit:
            git(d, "add", "-A")
            git(d, "commit", "-q", "-m", "edit " + fname)


class ValidateTests(Base):
    def test_sample_is_valid(self):
        self.assertEqual(eco.validate(self.reg), [])

    def test_catches_problems(self):
        r = copy.deepcopy(self.reg)
        r["projects"][0]["serves"] = ["nope"]
        r["projects"][2]["confirmed"] = [{"text": "x", "source": "u", "evidenceKind": "code"}]
        r["projects"][1]["purpose"] = "см. https://github.com/velantrian/alpha-typo/blob/main/README.md"
        r["projects"][0]["confirmed"][0]["evidenceKind"] = "doc-only"
        r["groups"][0]["projects"] = ["alpha", "alpha", "secret"]
        r["relations"][0]["level"] = "verified"
        r["relations"][0]["source"] = "нет ссылки"
        errs = "\n".join(eco.validate(r))
        for needle in ("неизвестная цель", "приватного проекта не должно быть confirmed", "alpha-typo",
                       "без вида основания", "ровно в одну группу", "verified требует ссылку"):
            self.assertIn(needle, errs)

    def test_why_and_role_are_required_unless_title_only(self):
        r = copy.deepcopy(self.reg)
        r["projects"][0]["why_exists"] = ""
        r["projects"][1]["role_in_concept"] = ""
        errs = "\n".join(eco.validate(r))
        self.assertIn("пустое поле 'why_exists'", errs)
        self.assertIn("пустое поле 'role_in_concept'", errs)
        r = copy.deepcopy(self.reg)
        r["projects"][2].update(title_only=True, purpose="", why_exists="", role_in_concept="")
        self.assertEqual(eco.validate(r), [])

    def test_private_may_not_record_sha_or_watch(self):
        r = copy.deepcopy(self.reg)
        r["projects"][2]["checked"]["ref"] = "main@123"
        r["projects"][2]["watch"]["purpose"] = ["README.md"]
        errs = "\n".join(eco.validate(r))
        self.assertIn("не записываем SHA", errs)
        self.assertIn("нет наблюдаемых файлов", errs)


SKELETON = """# Заголовок (ручной)

Ручное вступление с [ссылкой](https://example.org/manual).

<!-- ECOSYSTEM:BEGIN overview -->
<!-- ECOSYSTEM:END overview -->

<!-- ECOSYSTEM:BEGIN routes -->
старое
<!-- ECOSYSTEM:END routes -->

## Ручной раздел

Ручной текст между блоками.

<!-- ECOSYSTEM:BEGIN projects -->
<!-- ECOSYSTEM:END projects -->
<!-- ECOSYSTEM:BEGIN relations -->
<!-- ECOSYSTEM:END relations -->

Ручной абзац перед источниками.

<!-- ECOSYSTEM:BEGIN credits -->
<!-- ECOSYSTEM:END credits -->
<!-- ECOSYSTEM:BEGIN sources -->
<!-- ECOSYSTEM:END sources -->

Ручной хвост.
"""


class RenderTests(Base):
    def paths(self):
        rp, cp = self.t / "R.md", self.t / "C.md"
        rp.write_text(SKELETON, encoding="utf-8")
        return rp, cp, ["--registry", str(self.reg_path), "--readme-out", str(rp), "--catalog-out", str(cp),
                        "--relations-out", str(self.t / "REL.md")]

    def test_render_fills_only_blocks_and_keeps_manual_text(self):
        rp, cp, base = self.paths()
        self.assertEqual(run(["render"] + base)[0], 0)
        text = rp.read_text()
        for manual in ("# Заголовок (ручной)", "[ссылкой](https://example.org/manual)", "## Ручной раздел",
                       "Ручной текст между блоками.", "Ручной абзац перед источниками.", "Ручной хвост."):
            self.assertIn(manual, text)
        self.assertNotIn("старое", text)
        self.assertIn("[Alpha](https://github.com/velantrian/Alpha/blob/main/README.md)", text)
        self.assertIn("Делает альфу.", text)

    def test_render_is_idempotent_and_check_detects_stale_blocks(self):
        rp, cp, base = self.paths()
        self.assertEqual(run(["render"] + base)[0], 0)
        first = (rp.read_text(), cp.read_text())
        self.assertEqual(run(["render"] + base)[0], 0)
        self.assertEqual(first, (rp.read_text(), cp.read_text()))
        self.assertEqual(run(["render", "--check"] + base)[0], 0)
        self.reg["projects"][0]["purpose"] = "Изменили назначение."
        eco.dump_json(self.reg_path, self.reg)
        code, out = run(["render", "--check"] + base)
        self.assertEqual(code, 1)
        self.assertIn("УСТАРЕЛО", out)
        self.assertEqual(run(["render"] + base)[0], 0)
        self.assertEqual(run(["render", "--check"] + base)[0], 0)

    def test_editing_manual_text_does_not_break_check_and_survives_render(self):
        rp, cp, base = self.paths()
        run(["render"] + base)
        rp.write_text(rp.read_text().replace("Ручной хвост.", "Новый ручной хвост с [ссылкой](https://example.org/new)."), encoding="utf-8")
        self.assertEqual(run(["render", "--check"] + base)[0], 0)
        self.reg["projects"][1]["purpose"] = "Другое назначение беты."
        eco.dump_json(self.reg_path, self.reg)
        self.assertEqual(run(["render"] + base)[0], 0)
        self.assertIn("Новый ручной хвост с [ссылкой](https://example.org/new).", rp.read_text())

    def test_hand_edit_inside_generated_block_is_detected(self):
        rp, cp, base = self.paths()
        run(["render"] + base)
        rp.write_text(rp.read_text().replace("Делает альфу.", "Правка руками внутри блока."), encoding="utf-8")
        code, out = run(["render", "--check"] + base)
        self.assertEqual(code, 1)
        self.assertIn("УСТАРЕЛО", out)

    def test_missing_readme_or_marker_is_an_error_not_a_silent_rewrite(self):
        rp, cp, base = self.paths()
        rp.unlink()
        code, out = run(["render"] + base)
        self.assertEqual(code, 1)
        self.assertIn("нет R.md", out)
        rp.write_text(SKELETON.replace("<!-- ECOSYSTEM:BEGIN sources -->", "").replace("<!-- ECOSYSTEM:END sources -->", ""), encoding="utf-8")
        before = rp.read_text()
        code, out = run(["render"] + base)
        self.assertEqual(code, 1)
        self.assertIn("нет блока", out)
        self.assertEqual(rp.read_text(), before)

    def test_blocks_follow_registry_and_do_not_invent_integration(self):
        blocks = eco.render_blocks(self.reg)
        catalog = eco.render_catalog(self.reg)
        for p in self.reg["projects"]:
            self.assertIn(p["name"], blocks["projects"])
            self.assertIn('<a id="p-%s"></a>' % p["id"], catalog)
        self.assertIn("экзокортекс", blocks["projects"])
        self.assertIn("проверенное совместное выполнение (не подтверждены в рамках этой проверки)", blocks["relations"])
        self.assertIn("реализованный интерфейс (не подтверждены в рамках этой проверки)", blocks["relations"])
        self.assertIn("запланированная интеграция (в реестре: 1)", blocks["relations"])  # verified нет → не рисуем «работающую интеграцию»
        self.assertIn("-.->", blocks["relations"])  # planned — только пунктир
        self.assertNotIn("==>", blocks["relations"])
        # концептуальная связь alpha→beta не попадает в таблицу README, но есть в карточках
        self.assertNotIn("описано ([источник]", blocks["relations"])
        self.assertIn("Концептуальных связей (границы ответственности и общие идеи без плана и интерфейса): 1.", blocks["relations"])
        self.assertIn("описано", catalog)
        self.assertIn("автоматически не проверяется", catalog)
        self.assertIn("**Зачем существует.** Чтобы была альфа.", catalog)
        self.assertIn("**Роль в замысле.** Часть памяти.", catalog)

    def test_route_labels_name_the_document_when_a_project_repeats(self):
        self.reg["routes"][0]["answers"].append({"id": "alpha", "doc": "https://github.com/velantrian/Alpha/blob/main/NOTES.md", "why": "второе"})
        routes = eco.render_blocks(self.reg)["routes"]
        self.assertIn("[Alpha · NOTES.md](https://github.com/velantrian/Alpha/blob/main/NOTES.md)", routes)
        self.assertIn("[Alpha · README.md](https://github.com/velantrian/Alpha/blob/main/README.md)", routes)

    def test_confirmed_is_split_by_kind_and_run_needs_version(self):
        catalog = eco.render_catalog(self.reg)
        self.assertIn("*Механизм найден в коде:*", catalog)
        self.assertIn("*Есть запись успешного запуска с версией и условиями:*", catalog)
        self.assertIn("одно основание не подменяет другое", catalog)
        r = copy.deepcopy(self.reg)
        r["projects"][0]["confirmed"][1]["text"] = "Запуск прошёл."
        self.assertIn("запись запуска» без версии", "\n".join(eco.validate(r)))

    def test_overview_is_compact_and_relations_file_separates_levels(self):
        blocks = eco.render_blocks(self.reg)
        self.assertIn("| Проект | Тип | Для чего (коротко) | Чему служит |", blocks["overview"])
        self.assertIn("Делает альфу.", blocks["overview"])
        rel = eco.render_relations(self.reg)
        self.assertLess(rel.index("## План"), rel.index("## Концепция"))
        self.assertIn("_Связи этого уровня не подтверждены в рамках этой проверки._", rel)
        self.assertIn("не доказанное отсутствие связей во всей экосистеме", rel)

    def test_credits_are_rendered_and_validated(self):
        self.reg["meta"]["credits"] = [{"project": "alpha", "source": "[Upstream](https://github.com/Up/Alpha)", "kind": "fork-upstream",
                                        "note": "лицензия родителя не установлена", "evidence": ""}]
        self.reg["meta"]["excluded_third_party"] = [{"name": "ladybug", "url": "https://github.com/velantrian/ladybug", "note": "форк"}]
        self.assertEqual(eco.validate(self.reg), [])
        credits = eco.render_blocks(self.reg)["credits"]
        self.assertIn("лицензия родителя не установлена", credits)
        self.assertIn("исключённые из активной карты и мониторинга (не удалены", credits)
        self.reg["meta"]["credits"][0]["project"] = "nope"
        self.assertIn("заимствование: неизвестный проект", "\n".join(eco.validate(self.reg)))

    def test_purpose_markup_and_links_are_preserved_verbatim(self):
        self.reg["projects"][0]["purpose"] = "Текст с [ссылкой](https://github.com/velantrian/Beta/blob/main/README.md) и \\| уже экранированной чертой."
        blocks = eco.render_blocks(self.reg)
        self.assertIn("[ссылкой](https://github.com/velantrian/Beta/blob/main/README.md)", blocks["projects"])
        self.assertIn("\\| уже экранированной", blocks["projects"])
        self.assertNotIn("\\\\|", blocks["projects"])


class CheckTests(Base):
    def baseline(self):
        self.assertEqual(run(self.argv("baseline"))[0], 0)

    def check(self, *extra):
        return run(self.argv("check", *extra, "--no-cross"))

    def test_no_change_and_private_not_read(self):
        self.baseline()
        base = eco.load_json(self.base_path)
        self.assertNotIn("secret", base["projects"])
        code, out = self.check()
        self.assertEqual(code, 0)
        self.assertIn("NO CHANGE", out)
        self.assertIn("приватный репозиторий", out)

    def test_no_change_never_claims_full_coverage(self):
        self.baseline()
        code, out = self.check()
        self.assertEqual(code, 0)
        self.assertIn("NO CHANGE (только в проверенных источниках)", out)
        self.assertIn("это не полный охват", out)
        summary = self.t / "s.md"
        self.check("--summary", str(summary))
        text = summary.read_text()
        self.assertIn("проверено 2 из 3 проектов", text)
        self.assertIn("NO CHANGE не означает полного охвата", text)

    def test_change_stays_visible_until_baseline_is_explicitly_accepted(self):
        self.baseline()
        self.edit("Alpha", "README.md", "# Alpha\n\nНовое назначение.\n")
        for _ in range(3):
            self.assertEqual(self.check()[0], 10)  # повторные check без baseline продолжают показывать изменение
        self.baseline()  # только явное принятие новой базы убирает расхождение
        self.assertEqual(self.check()[0], 0)

    def test_technical_commits_are_ignored(self):
        self.baseline()
        self.edit("Alpha", "code.py", "print(1)\n")  # коммит не затрагивает наблюдаемые файлы
        code, out = self.check()
        self.assertEqual(code, 0)
        self.assertIn("NO CHANGE", out)

    def test_whitespace_only_is_technical(self):
        self.baseline()
        self.edit("Alpha", "README.md", "# Alpha\n\n\nНазначение   исходное.\n\n")
        code, out = self.check()
        self.assertEqual(code, 0)
        self.assertIn("только форматирование", out)

    def test_purpose_change_needs_review_with_diff(self):
        self.baseline()
        self.edit("Alpha", "README.md", "# Alpha\n\nТеперь это совсем другой проект.\n")
        code, out = self.check()
        self.assertEqual(code, 10)
        self.assertIn("ТРЕБУЕТ РАССМОТРЕНИЯ", out)
        self.assertIn("-Назначение исходное.", out)
        self.assertIn("+Теперь это совсем другой проект.", out)
        self.assertIn("автоматически не менялись", out)
        self.assertEqual(eco.load_json(self.reg_path), self.reg)  # реестр не тронут
        # повторный запуск без новых изменений показывает то же (baseline не принимался сам)
        self.assertEqual(self.check()[0], 10)
        # после явного baseline — снова NO CHANGE
        self.baseline()
        self.assertEqual(self.check()[0], 0)

    def test_status_doc_change_is_not_a_status_upgrade(self):
        self.baseline()
        self.edit("Alpha", "STATUS.md", "status: production-ready\n")
        code, out = self.check()
        self.assertEqual(code, 10)
        self.assertIn("явный статус или интерфейс", out)
        self.assertIn("не повышается", out)

    def test_metadata_changes(self):
        self.baseline()
        self.set_meta("velantrian/Alpha", archived=True)
        self.set_meta("velantrian/Beta", full_name="velantrian/Beta-Renamed")
        code, out = self.check()
        self.assertEqual(code, 10)
        self.assertIn("архивирование", out)
        self.assertIn("имя репозитория", out)
        self.set_meta("velantrian/Alpha", archived=False)
        self.set_meta("velantrian/Beta", full_name="velantrian/Beta", description="Новое описание")
        code, out = self.check()
        self.assertEqual(code, 10)
        self.assertIn("описание на GitHub", out)

    def test_missing_repo_and_unreadable_repo(self):
        self.baseline()
        self.set_meta("velantrian/Alpha", status="missing")
        self.set_meta("velantrian/Beta", status="forbidden", detail="HTTP 403")
        code, out = self.check()
        self.assertEqual(code, 10)  # Alpha пропал
        self.assertIn("не найден", out)
        self.assertIn("не проверено: HTTP 403", out)  # Beta — не изменение, а «не проверено»

    def test_unreadable_alone_is_not_a_change(self):
        self.baseline()
        self.set_meta("velantrian/Beta", status="rate-limited", detail="лимит запросов API")
        code, out = self.check()
        self.assertEqual(code, 0)
        self.assertIn("Не проверено", out)

    def test_baseline_gaps_are_not_changes(self):
        self.meta["velantrian/Alpha"].update(archived=None, description=None)
        eco.dump_json(self.meta_path, self.meta)
        self.baseline()
        self.meta["velantrian/Alpha"].update(archived=False, description="Описание")
        eco.dump_json(self.meta_path, self.meta)
        code, out = self.check()
        self.assertEqual(code, 0)
        self.assertIn("Нет базовой отметки", out)

    def test_baseline_keeps_previous_when_unreadable(self):
        self.baseline()
        before = eco.load_json(self.base_path)["projects"]["alpha"]
        self.set_meta("velantrian/Alpha", status="forbidden", detail="HTTP 403")
        self.baseline()
        self.assertEqual(eco.load_json(self.base_path)["projects"]["alpha"], before)

    def test_missing_watched_file_is_reported_and_baseline_keeps_old_fingerprint(self):
        self.baseline()
        before = eco.load_json(self.base_path)["projects"]["beta"]["files"]["README.md"]
        (Path(self.clones["velantrian/Beta"]) / "README.md").unlink()
        code, out = self.check()
        self.assertEqual(code, 10)
        self.assertIn("файл README.md отсутствует", out)
        self.baseline()  # пропавший файл не должен стирать прежнюю отметку
        self.assertEqual(eco.load_json(self.base_path)["projects"]["beta"]["files"]["README.md"], before)

    def test_long_diff_is_truncated(self):
        self.baseline()
        self.edit("Alpha", "README.md", "\n".join("строка %d" % i for i in range(200)) + "\n")
        code, out = self.check()
        self.assertEqual(code, 10)
        self.assertIn("… (ещё", out)
        self.assertLess(len(out.splitlines()), 150)

    def test_workflow_command_injection_is_neutralised(self):
        # строки diff всегда начинаются с +/-/пробела, поэтому защиту проверяем и напрямую, и сквозным запуском
        self.assertEqual(eco.safe_line("::set-output name=x::y"), " ::set-output name=x::y")
        self.assertEqual(eco.safe_line("обычная строка"), "обычная строка")
        self.baseline()
        self.edit("Alpha", "README.md", "# Alpha\n\n::set-output name=x::y\n::warning::boom\n")
        code, out = self.check()
        self.assertEqual(code, 10)
        self.assertFalse([l for l in out.splitlines() if l.startswith("::")])

    def test_summary_and_proposal_files(self):
        self.baseline()
        self.edit("Alpha", "README.md", "# Alpha\n\nИное.\n")
        summary, proposal, js = self.t / "s.md", self.t / "p.json", self.t / "r.json"
        code, out = self.check("--summary", str(summary), "--propose", str(proposal), "--json", str(js))
        self.assertEqual(code, 10)
        self.assertIn("Alpha", summary.read_text())
        self.assertEqual(eco.load_json(js)["review"], 1)
        old = eco.load_json(self.base_path)["projects"]["alpha"]["files"]["README.md"]["blob"]
        new = eco.load_json(proposal)["projects"]["alpha"]["files"]["README.md"]["blob"]
        self.assertNotEqual(old, new)  # предложение отличается, а сам baseline не изменён
        self.assertEqual(eco.load_json(self.base_path)["projects"]["alpha"]["files"]["README.md"]["blob"], old)


class CrossCheckTests(Base):
    def setUp(self):
        super().setUp()
        atlas, vel = self.t / "atlas", self.t / "vel"
        (atlas / "atlas").mkdir(parents=True)
        (vel / "tools" / "ecosystem-evidence").mkdir(parents=True)
        eco.dump_json(atlas / "atlas" / "projects.json", {"projects": [{"id": "alpha"}, {"id": "area-x"}, {"id": "orphan"}]})
        eco.dump_json(atlas / "atlas" / "sources.json", {"sources": [
            {"id": "a-gh", "url": "https://github.com/velantrian/alpha"},   # другое написание
            {"id": "b-gh", "url": "https://github.com/velantrian/Beta"}]})
        eco.dump_json(vel / "tools" / "ecosystem-evidence" / "ecosystem_status_index.json", {"projects": [
            {"id": "alpha", "repo": "velantrian/Alpha"}, {"id": "gone", "repo": "velantrian/Renamed"}]})
        self.clones["velantrian/Velantrim-Atlas-App"] = str(atlas)
        self.clones["velantrian/velantrim"] = str(vel)
        eco.dump_json(self.map_path, self.clones)

    def notes(self):
        reg = copy_registry(self.reg)
        return eco.cross_check(reg, eco.LocalTransport(self.clones))

    def test_atlas_and_index_drift(self):
        texts = [t for _, t in self.notes()]
        joined = "\n".join(texts)
        self.assertIn("«orphan»", joined)                    # есть в Atlas, нет в реестре
        self.assertIn("«a-gh» записан как velantrian/alpha, точное имя — velantrian/Alpha", joined)
        self.assertIn("velantrian/Renamed", joined)          # индекс evidence ссылается на неизвестное имя
        self.assertNotIn("«b-gh»", joined)                   # написание совпадает

    def test_known_areas_are_silent_and_unknown_id_is_review(self):
        self.reg["meta"]["atlas_areas"] = {"area-x": "область без репозитория"}
        self.reg["projects"][1]["cross"] = {"atlas": "missing-id"}
        notes = eco.cross_check(copy_registry(self.reg), eco.LocalTransport(self.clones))
        joined = "\n".join(t for _, t in notes)
        self.assertNotIn("«area-x»", joined)
        self.assertIn(("review", "Atlas: проект «Beta» ссылается на id «missing-id», которого нет в atlas/projects.json"), notes)

    def test_unavailable_neighbours_are_not_changes(self):
        notes = eco.cross_check(copy_registry(self.reg), eco.LocalTransport({}))
        self.assertTrue(notes)
        self.assertTrue(all(kind == "info" for kind, _ in notes))


def copy_registry(reg):
    return json.loads(json.dumps(reg))


if __name__ == "__main__":
    unittest.main()
