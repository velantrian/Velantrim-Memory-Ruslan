# tools/ecosystem — реестр проектов и проверка источников

Единственный редактируемый источник данных о проектах — [`projects/ecosystem.json`](../../projects/ecosystem.json). Из него формируются участки [`projects/README.md`](../../projects/README.md) (между маркерами `ECOSYSTEM:BEGIN … ECOSYSTEM:END`) и весь файл [`projects/ecosystem-catalog.md`](../../projects/ecosystem-catalog.md). Остальной текст `projects/README.md` — ручной и командами не затрагивается.

Скрипт использует только стандартную библиотеку Python 3, не вызывает платные API и LLM, не требует новых секретов, ничего не коммитит и не создаёт PR или issues.

## Что кто редактирует

| Файл или участок | Кто |
|---|---|
| `projects/ecosystem.json` | человек (после чтения первоисточника) |
| `projects/README.md`, текст вне маркеров | человек |
| `projects/README.md`, блоки между маркерами | формируется командой `render` |
| `projects/ecosystem-catalog.md` | формируется целиком |
| `projects/ecosystem-baseline.json` | командой `baseline`, только после рассмотрения изменений |

## Команды

```bash
python3 tools/ecosystem/ecosystem.py validate         # схема, точные имена репозиториев, правила приватности
python3 tools/ecosystem/ecosystem.py render           # заполнить блоки README и карточки из реестра
python3 tools/ecosystem/ecosystem.py render --check   # только проверить, что файлы соответствуют реестру
python3 tools/ecosystem/ecosystem.py check            # сравнить источники с baseline (только чтение)
python3 tools/ecosystem/ecosystem.py baseline         # записать отпечатки (явная команда, после рассмотрения)
python3 -I -m unittest discover -s tools/ecosystem    # тесты
```

Локально без Actions: `check --transport gh` (нужен вход в `gh`). Коды выхода: 0 — всё в порядке или NO CHANGE; 1 — проблема в `validate`/`render --check`; 10 — есть изменения для рассмотрения; 2 — ошибка запуска.

## Что отслеживает `check`

- переименование (в том числе смена регистра), архивирование, видимость, доступность и описание репозитория;
- документы о назначении и явно опубликованный статус или интерфейс (список — поле `watch` у проекта);
- согласованность с Atlas (`atlas/projects.json`, `sources.json`) и индексом `velantrim/tools/ecosystem-evidence` (только сообщает).

Технические коммиты, которые не трогают эти источники, не отслеживаются. Если изменилось только форматирование файла, это «техническое» и решения не требует. Автоматика не повышает статус реализации: новое описание — повод проверить карточку, а не доказательство. Приватные репозитории не читаются и отмечаются «не проверено».

Результат — раздел Summary запуска, артефакт `ecosystem-report.json` и предлагаемый baseline `proposed-baseline.json`. Если значимых изменений нет, результат — NO CHANGE и ничего больше не происходит.

## Как включить проверку

1. Merge изменения (решение владельца): workflow с ручным запуском появляется в ветке по умолчанию.
2. Actions → Ecosystem check → Run workflow (режим `check`). Прочитать Summary. Для репозиториев, у которых в baseline нет метаданных (`null`), будет раздел «Нет базовой отметки» — это не изменение; предложенный baseline можно применить отдельным согласованным изменением.
3. Запустить ещё раз: ожидается NO CHANGE.
4. Только после этого включить расписание: раскомментировать блок `schedule` в `.github/workflows/ecosystem-check.yml` (раз в неделю). Права только `contents: read`, секреты не нужны (используется встроенный токен запуска).
5. Рассмотрение изменений: открыть источник, решить, нужна ли правка `ecosystem.json`; затем `render`, затем `baseline` и отдельный Draft PR по процедуре Safe Memory Update (`START_HERE.md`).

Не включено и в этот PR не входит: автоматическое создание PR или issues и внешние уведомления. Их можно добавить позже отдельным решением (понадобятся права `pull-requests: write` / `issues: write`).
