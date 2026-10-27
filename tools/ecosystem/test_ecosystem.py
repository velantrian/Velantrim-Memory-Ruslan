"""Тесты tools/ecosystem/ecosystem.py на локальных фикстурах (без сети).

Запуск: python3 -m unittest discover -s tools/ecosystem -v
"""
import contextlib
import copy
import io
import json
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


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = Path(self.tmp.name)
        self.reg_path = self.t / "ecosystem.json"
        self.reg = sample_registry()
        eco.dump_json(self.reg_path, self.reg)

    def tearDown(self):
        self.tmp.cleanup()


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
        r["projects"][2].update(title_only=True, repo="", purpose="", why_exists="", role_in_concept="")
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
        return rp, cp, ["--registry", str(self.reg_path), "--readme-out", str(rp), "--catalog-out", str(cp)]

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
        # план показан в таблице, концептуальная связь alpha→beta — нет; её описание остаётся в карточках
        self.assertIn("| Beta | Alpha | План |", blocks["relations"])
        self.assertNotIn("описано ([источник]", blocks["relations"])
        self.assertIn("Концептуальные связи (1:", blocks["relations"])
        self.assertIn("VELANTRIM_ECOSYSTEM_MASTER_MAP.md", blocks["relations"])
        self.assertNotIn("mermaid", blocks["relations"])
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

    def test_overview_is_compact_and_routes_point_to_atlas(self):
        blocks = eco.render_blocks(self.reg)
        self.assertIn("| Проект | Тип | Для чего (коротко) | Чему служит |", blocks["overview"])
        self.assertIn("Делает альфу.", blocks["overview"])
        self.assertIn("Atlas", blocks["routes"])
        self.assertIn("atlas/routes.json", blocks["routes"])
        self.assertIn("не отдельный маршрутизатор", blocks["routes"])

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

    def title_only_with_repo(self):
        # синтетический идентификатор: настоящих приватных slug в тестах нет
        self.reg["projects"].append({
            "id": "hidden", "name": "Скрытая книга", "repo": "velantrian/Synthetic-Private-Repo-123", "visibility": "private",
            "type": "docs", "title_only": True, "purpose": "", "why_exists": "", "role_in_concept": "", "serves": [], "confirmed": [],
            "planned": [], "limits": "", "entry_doc": "", "status_doc": "", "history": [], "watch": {"purpose": [], "status": []},
            "checked": {"date": "2026-10-21", "ref": "", "basis": []}})
        self.reg["groups"][0]["projects"].append("hidden")

    def test_title_only_with_repo_id_is_rejected_by_validate(self):
        self.title_only_with_repo()
        errs = "\n".join(eco.validate(self.reg))
        self.assertIn("у записи title_only не должно быть поля 'repo'", errs)
        self.assertNotIn("hidden", errs)

    def test_title_only_rejects_other_identifiers_and_urls(self):
        self.title_only_with_repo()
        p = self.reg["projects"][-1]
        p["repo"] = ""
        p["limits"] = "см. https://github.com/velantrian/Synthetic-Private-Repo-123"
        self.assertIn("идентификатора или ссылки на репозиторий", "\n".join(eco.validate(self.reg)))
        p["limits"], p["entry_doc"] = "", "https://example.org/x"
        self.assertIn("не должно быть поля 'entry_doc'", "\n".join(eco.validate(self.reg)))

    def test_title_only_never_renders_repo_id_even_if_it_reaches_renderer(self):
        self.title_only_with_repo()
        self.reg["projects"][-1]["entry_doc"] = "https://github.com/velantrian/Synthetic-Private-Repo-123/blob/main/README.md"
        blocks, catalog = eco.render_blocks(self.reg), eco.render_catalog(self.reg)
        for text in list(blocks.values()) + [catalog]:
            self.assertNotIn("Synthetic-Private-Repo-123", text)
        self.assertIn("Скрытая книга", blocks["overview"])
        self.assertIn('<a id="p-titleonly-1"></a>', catalog)

    def test_title_only_render_via_cli_leaves_no_repo_id_in_files(self):
        self.title_only_with_repo()
        self.reg["projects"][-1]["repo"] = ""  # валидная запись; идентификатор не должен появиться и в файлах
        eco.dump_json(self.reg_path, self.reg)
        rp, cp, base = self.paths()
        self.assertEqual(run(["render"] + base)[0], 0)
        self.assertNotIn("Synthetic-Private-Repo-123", rp.read_text() + cp.read_text())

    def test_title_only_id_cannot_leak_through_anchor_or_links(self):
        self.title_only_with_repo()
        p = self.reg["projects"][-1]
        p["repo"], p["id"] = "", "synthetic-private-repo-123"
        self.reg["groups"][0]["projects"][-1] = p["id"]
        self.reg["relations"].append({"from": "alpha", "to": p["id"], "kind": "related", "level": "conceptual", "basis": "описано",
                                      "source": "https://github.com/velantrian/Alpha/blob/main/README.md"})
        self.assertIn("id не должен напоминать имя репозитория", "\n".join(eco.validate(self.reg)))
        # даже если невалидная запись дошла до рендерера, id не попадает ни в якорь, ни в ссылки, ни в текст
        blocks, catalog = eco.render_blocks(self.reg), eco.render_catalog(self.reg)
        for text in list(blocks.values()) + [catalog]:
            self.assertNotIn("synthetic-private-repo-123", text)
        self.assertIn('<a id="p-titleonly-1"></a>', catalog)
        self.assertIn("(#p-titleonly-1)", catalog)  # ссылка из связи ведёт на нейтральный якорь
        self.assertIn("ecosystem-catalog.md#p-titleonly-1", blocks["overview"])

    def test_title_only_id_must_not_contain_repo_name(self):
        self.title_only_with_repo()
        p = self.reg["projects"][-1]
        p["id"], p["repo"] = "mysyntheticrepo", "velantrian/SyntheticRepo"
        self.reg["groups"][0]["projects"][-1] = p["id"]
        self.assertIn("id не должен напоминать имя репозитория", "\n".join(eco.validate(self.reg)))

    def test_empty_description_fallback_does_not_attribute_a_decision_to_the_owner(self):
        self.title_only_with_repo()
        self.reg["projects"][-1]["repo"] = ""
        catalog = eco.render_catalog(self.reg)
        self.assertIn("**Назначение.** описание не предоставлено", catalog)
        self.assertNotIn("по решению владельца", catalog)
        self.assertNotIn("решение владельца", catalog)

    def test_title_only_anchor_cannot_collide_with_a_regular_project_id(self):
        self.title_only_with_repo()
        self.reg["projects"][-1]["repo"] = ""
        regular = copy.deepcopy(self.reg["projects"][1])  # beta
        regular["id"], regular["name"] = "titleonly-1", "Обычный проект"
        self.reg["projects"].append(regular)
        self.reg["groups"][0]["projects"].append("titleonly-1")
        errs = "\n".join(eco.validate(self.reg))
        self.assertIn("коллизия якорей карточек: 'p-titleonly-1'", errs)
        self.assertNotIn("hidden", errs)  # сообщение не называет id записи title_only

    def test_title_only_anchors_follow_registry_order(self):
        # ограничение: нейтральные якоря нумеруются по порядку записей, перестановка меняет номера
        self.title_only_with_repo()
        self.reg["projects"][-1]["repo"] = ""
        second = copy.deepcopy(self.reg["projects"][-1])
        second["id"], second["name"] = "hiddenb", "Вторая скрытая"
        self.reg["projects"].append(second)
        self.reg["groups"][0]["projects"].append("hiddenb")
        before = eco.anchors(self.reg)
        self.assertEqual((before["hidden"], before["hiddenb"]), ("p-titleonly-1", "p-titleonly-2"))
        self.reg["projects"][-2], self.reg["projects"][-1] = self.reg["projects"][-1], self.reg["projects"][-2]
        after = eco.anchors(self.reg)
        self.assertEqual((after["hidden"], after["hiddenb"]), ("p-titleonly-2", "p-titleonly-1"))
        self.assertEqual(eco.validate(self.reg), [])


    def test_title_only_group_validation_never_exposes_id(self):
        self.title_only_with_repo()
        self.reg["projects"][-1]["repo"] = ""
        self.reg["groups"][0]["projects"].pop()
        errs = "\n".join(eco.validate(self.reg))
        self.assertIn("ровно в одну группу", errs)
        self.assertNotIn("hidden", errs)

    def test_title_only_case_variant_github_url_is_rejected_before_render(self):
        self.title_only_with_repo()
        self.reg["projects"][-1]["repo"] = ""
        self.reg["projects"][-1]["limits"] = "https://GITHUB.com/VELANTRIAN/Synthetic-Private-Repo-123"
        errs = "\n".join(eco.validate(self.reg))
        self.assertIn("идентификатора или ссылки на репозиторий", errs)
        self.assertNotIn("VELANTRIAN/Synthetic-Private-Repo-123", errs)
        eco.dump_json(self.reg_path, self.reg)
        rp, cp, base = self.paths()
        self.assertEqual(run(["render"] + base)[0], 1)
        self.assertFalse(cp.exists())

    def test_title_only_invalid_id_does_not_enter_validation_errors(self):
        self.title_only_with_repo()
        p = self.reg["projects"][-1]
        p["id"] = "synthetic-private-repo-123"
        self.reg["groups"][0]["projects"][-1] = p["id"]
        errs = "\n".join(eco.validate(self.reg))
        self.assertIn("id не должен напоминать имя репозитория", errs)
        self.assertNotIn("synthetic-private-repo-123", errs)


if __name__ == "__main__":
    unittest.main()
