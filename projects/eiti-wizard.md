# Eiti Wizard — карточка проекта

- **PROJECT:** Eiti Wizard
- **AS_OF:** 2026-10-08
- **CURRENT_GOAL:** Сохранить рабочее состояние направления переносимой памяти без продолжения разработки PWA в рамках текущего задания.
- **CURRENT_STATUS:** `WORK PAUSE / FROZEN DEVELOPMENT SCOPE` для переносимой памяти и PWA Working Memory. Это не заморозка всех работ Eiti, не merge-решение и не оценка production-готовности.

## Подтверждённое состояние

- Приватный репозиторий [`velantrian/Eiti-Wizard-Lab-2`](https://github.com/velantrian/Eiti-Wizard-Lab-2) имеет `main` SHA `649c7fd7673aceb3abdefee2a3fa3d96cdf6935d` (GitHub API, проверено 2026-10-08).
- [PR #1 — Portable Continuity Memory](https://github.com/velantrian/Eiti-Wizard-Lab-2/pull/1): `OPEN / DRAFT / NOT MERGED`; head `6283dd037e88995556352e7c57bd779fdb7cb270`. Его описание говорит, что это документационное изменение; fresh-chat resume и подтверждённый save/read-back после owner review и merge не проверены. Cross-provider совместимость не проверялась.
- [PR #2 — PWA Working Memory B2](https://github.com/velantrian/Eiti-Wizard-Lab-2/pull/2): `OPEN / DRAFT / NOT MERGED / NOT_READY_FOR_MERGE`; head `8711a42be25ec95cfdeecd610262fc3c560e345d`. В описании PR перечислены локальные тесты на синтетических данных и stub-провайдерах; live DeepSeek/Gemini call, deployment и внешний sync не выполнялись. Это содержание описания PR, не независимый повтор тестов в этой задаче.
- В текущем описании PR #2 независимый read-only аудит и ручная телефонная приёмка остаются незавершёнными. Телефонная проверка должна подтвердить фактический provider request и поведение toggle; до этого не повышать статус до ready.
- В задание владельца включён кандидатный риск будущего аудита B2: распознавание выбора по словам и ID варианта может неправильно трактовать составную фразу вроде “I choose A, not B”. Это зафиксировано как **непроверенный audit target**, а не как воспроизведённый дефект. Код PWA в этом задании не расширялся.

## Решения владельца и границы

**OWNER_DECISIONS:** Перенести приоритет с PWA-памяти на отдельную универсальную GitHub-память; приостановить именно направление переносимой памяти/PWA Working Memory. Сохранить существующие ветки и документы. Не делать merge, не закрывать PR, не удалять ветви, не менять Canon/seed/manifest/runtime и не развёртывать PWA. Возобновление — только по отдельному решению владельца. Источник: задание владельца от 2026-10-08, §§2 и 17.

**UNDECIDED:** Дата и объём будущего возобновления не определены. Переход от Draft к Ready/Merged не разрешён текущим заданием.

**OPEN_QUESTIONS:** Успешны ли независимый аудит PR #2 и ручная телефонная приёмка — пока нет подтверждения завершения. Реальное межмодельное восстановление из GitHub — не тестировалось. Синтетические тесты не подтверждают поведение реальных моделей или межпровайдерную переносимость.

**BLOCKERS:** PR #2 явно отмечен `NOT_READY_FOR_MERGE`; аудит и phone acceptance pending. Для PR #1 fresh-chat resume и confirmed save/read-back остаются непроверенными. Ни один PR не следует merge-ить или закрывать на основании этой карточки.

**NEXT_ACTION:** Сохранять текущую паузу. При отдельном разрешении владельца на возобновление — сначала завершить независимый read-only аудит и ручную телефонную приёмку PR #2 и записать фактические результаты; это предложение следующего ограниченного шага, не действие, выполненное здесь.

**SOURCE_LINKS:** [Исходный репозиторий](https://github.com/velantrian/Eiti-Wizard-Lab-2); [PR #1](https://github.com/velantrian/Eiti-Wizard-Lab-2/pull/1); [PR #2](https://github.com/velantrian/Eiti-Wizard-Lab-2/pull/2); [`ACTIVE_WORKING_STATE.md` на head PR #1](https://github.com/velantrian/Eiti-Wizard-Lab-2/blob/6283dd037e88995556352e7c57bd779fdb7cb270/docs/memory/ACTIVE_WORKING_STATE.md); задание владельца от 2026-10-08, §§2.2–2.3, включая непроверенный audit target.

**LAST_VERIFIED:** GitHub API повторно проверил PR state, draft flag, merge state, base/main SHA и head SHA 2026-10-08. Состояние может измениться; сверяйте GitHub перед каждым новым решением.
