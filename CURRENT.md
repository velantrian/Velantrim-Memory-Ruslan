# CURRENT — рабочая ориентация

- **AS_OF:** 2026-10-09
- **LAST_VERIFIED:** GitHub проверен 2026-10-09: приватность и `main` целевого репозитория, его HEAD, исходный Memory PR #2 и Eiti Wizard PR #1/#2. HEAD `main` целевого репозитория: `faa91a93c6e5b2c1b7d8a329a2c5f08abe3cf782`. Статусы первичных источников могут измениться; сверяйте их перед действием. Notion-страницы и HLC-источники отдельно не перепроверялись в этой проверке; содержание Google Docs остаётся `NOT_VERIFIED_IN_THIS_SESSION`.
- **PROJECT:** Velantrim-Memory-Ruslan — целевая копия для этой задачи; это не решение сделать её единственным хранилищем всех будущих ИИ.

**CURRENT_GOAL:** Устойчивая цель — восстановление контекста между разными ИИ и безопасное сохранение согласованных изменений без отдельного runtime.

**CURRENT_STATUS:** Приватный репозиторий [`velantrian/Velantrim-Memory-Ruslan`](https://github.com/velantrian/Velantrim-Memory-Ruslan) создан; GitHub `main` доступен и указывает на HEAD выше. В `main` присутствуют документы памяти, две музыкальные MP3 и Git-история; в архивных refs сохранены ветки-источники. Последний commit `faa91a9` исправил две согласованные детали копии: ссылку Quick Start на новый репозиторий и длительность Karif Best Instrumental на 5:37. Перенесённые файлы и история подтверждают содержимое копии, но не восстановление контекста в новом независимом чате.

Для исходного [`velantrian/Velantrim-Memory`](https://github.com/velantrian/Velantrim-Memory) GitHub показывает, что [PR #2](https://github.com/velantrian/Velantrim-Memory/pull/2) слит 2026-10-09; merge commit — [`c7b1c04148f455a971998e25642e91e4a7579124`](https://github.com/velantrian/Velantrim-Memory/commit/c7b1c04148f455a971998e25642e91e4a7579124). README текущего `main` исходного репозитория указывает, что цикл PR → merge → read-back подтверждён для одного изменения. Его `CURRENT.md` всё ещё содержит прежние строки `NOT_RUN` и «ожидает merge»; это устаревшая контрольная точка, а не текущий статус PR. Утверждение о чтении в ChatGPT и Mistral остаётся `OWNER_REPORTED / TOOL_LOGS_NOT_INDEPENDENTLY_AUDITED`.

## Активные ориентиры

- **Eiti Wizard:** направление переносимой памяти / PWA Working Memory остаётся `WORK PAUSE`. В отдельном репозитории [PR #1](https://github.com/velantrian/Eiti-Wizard-Lab-2/pull/1) и [PR #2](https://github.com/velantrian/Eiti-Wizard-Lab-2/pull/2) проверены как `OPEN / DRAFT / NOT MERGED` 2026-10-09. Eiti PR #2 — не Memory PR #2.
- **HLC:** сохранённые исследовательские статусы и границы доказательств приведены в [`projects/hlc.md`](projects/hlc.md); в рамках этой проверки эксперименты не запускались.
- **Velantrim-Memory-Ruslan:** текущая цель — надёжные правила чтения и подготовки минимального изменения; состояние после возможного будущего merge нужно проверять отдельно.

**OWNER_DECISIONS:** Память должна быть отделена от приложения, модели и чат-сессии; GitHub выбран первоначальным хранилищем. Приоритет перенесён с PWA-памяти Eiti на независимую GitHub-память. Изменение памяти требует подтверждения конкретного diff; merge — отдельное решение владельца. Репозиторий Velantrim-Memory-Ruslan является целевым в этой задаче, но решение сделать его единственным основным репозиторием для всех будущих ИИ не принято. Исходный репозиторий не удалять и не объявлять архивным административно.

**UNDECIDED:** Будет ли Velantrim-Memory-Ruslan единственным основным хранилищем всех будущих ИИ; когда возобновится PWA; какой следующий эксперимент HLC выбрать.

**OPEN_QUESTIONS:** Для нового репозитория отдельно не подтверждены успешное восстановление в полностью новом независимом чате и полный цикл записи с read-back после merge. Универсальная совместимость со всеми ИИ не установлена. Содержание указанных Google Docs — `NOT_VERIFIED_IN_THIS_SESSION`; это не утверждение об их общей недоступности.

**BLOCKERS:** Независимый аудит и телефонная приёмка Eiti PR #2 остаются незавершёнными, но не блокируют работу с GitHub-памятью. Для этого изменения новых компонентов или сервисов не требуется.

**NEXT_ACTION:** После публикации этих правил следующий практический этап — независимый cold-read тест нового репозитория: до теста сверить фактическое состояние GitHub (`main`, его commit SHA и опубликованные правила), затем проверить восстановление контекста в новом независимом чате.

## Cold-read restoration tests

Источник результатов — отчёты владельца; при подготовке этой записи проверен GitHub `main` на `237b868a51b2bc59939d771c92d97cc2e37948b1` (2026-10-09).

- **Cold-Read-01 — ChatGPT 6** — `OWNER_REPORTED / REPORT_REVIEWED / RAW_TOOL_LOGS_NOT_AUDITED`: по отчёту владельца, доступ к приватному GitHub успешен; рабочая точка восстановлена; актуальные HEAD и PR определены правильно; правила безопасной записи объяснены; изменений в репозитории не выполнялось.
- **Cold-Read-02 — ChatGPT 6.1 Sol** — `OWNER_REPORTED / REPORT_REVIEWED / RAW_TOOL_LOGS_NOT_AUDITED`: по отчёту владельца, доступ к приватному GitHub успешен; рабочая точка восстановлена; актуальные HEAD и статусы PR определены правильно; подтверждённые факты отличены от неизвестного; изменений в репозитории не выполнялось.
- **Границы:** оба испытания проведены в ChatGPT; межпровайдерная переносимость — `NOT_ESTABLISHED`. Независимость чат-сессий и универсальная совместимость не доказаны. Полный цикл записи и восстановления в новом репозитории — `NOT_RUN`.

**SOURCE_LINKS:** [целевой репозиторий](https://github.com/velantrian/Velantrim-Memory-Ruslan); [его проверенный HEAD](https://github.com/velantrian/Velantrim-Memory-Ruslan/commit/faa91a93c6e5b2c1b7d8a329a2c5f08abe3cf782); [README исходной памяти](https://github.com/velantrian/Velantrim-Memory/blob/9c7366ec7f36da562416acfb3724a6393433daf7/README.md); [исторический CURRENT исходной памяти](https://github.com/velantrian/Velantrim-Memory/blob/9c7366ec7f36da562416acfb3724a6393433daf7/CURRENT.md); [`Eiti Wizard`](projects/eiti-wizard.md); [`HLC`](projects/hlc.md); [исходный репозиторий Eiti](https://github.com/velantrian/Eiti-Wizard-Lab-2); [Eiti PR #1](https://github.com/velantrian/Eiti-Wizard-Lab-2/pull/1); [Eiti PR #2](https://github.com/velantrian/Eiti-Wizard-Lab-2/pull/2); [Notion Experiment Registry](https://app.notion.com/p/3edac84d054781ad9634db49b600ad08); [Notion HLC-SPECTRUM-01](https://app.notion.com/p/3f2ac84d0547819c9306f3674727b42a).
