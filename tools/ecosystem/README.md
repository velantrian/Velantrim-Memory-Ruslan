# tools/ecosystem — реестр проектов

Единственный редактируемый источник данных о проектах — [`projects/ecosystem.json`](../../projects/ecosystem.json). Из него формируются блоки [`projects/README.md`](../../projects/README.md) (между маркерами `ECOSYSTEM:BEGIN … ECOSYSTEM:END`) и весь файл [`projects/ecosystem-catalog.md`](../../projects/ecosystem-catalog.md). Остальной текст `projects/README.md` — ручной.

Скрипт использует только стандартную библиотеку Python 3, работает локально: без сети, секретов, платных сервисов и LLM, ничего не коммитит.

| Файл или участок | Кто |
|---|---|
| `projects/ecosystem.json` | человек (после чтения первоисточника) |
| `projects/README.md`, текст вне маркеров | человек |
| `projects/README.md`, блоки между маркерами | формируется командой `render` |
| `projects/ecosystem-catalog.md` | формируется целиком |

```bash
python3 tools/ecosystem/ecosystem.py validate         # схема, точные имена репозиториев, правила приватности
python3 tools/ecosystem/ecosystem.py render           # заполнить блоки README и карточки из реестра
python3 tools/ecosystem/ecosystem.py render --check   # только проверить, что файлы соответствуют реестру
python3 -I -m unittest discover -s tools/ecosystem    # тесты
```

Коды выхода: 0 — всё в порядке; 1 — проблема; 2 — ошибка запуска.

Маршруты «вопрос → владелец» ведёт Atlas (`atlas/routes.json`), общую композицию — Master Map; реестр их не дублирует. Правки реестра идут по процедуре Safe Memory Update (`START_HERE.md`).
