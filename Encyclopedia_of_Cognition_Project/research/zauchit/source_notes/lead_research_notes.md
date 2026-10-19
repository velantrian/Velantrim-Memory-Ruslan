# Находки для синтеза Заучит

## Досье
Прочитаны основная часть 1–737, оригиналы S07, S13–S15. Пользователь просит глубокое исследование, не автоматический запуск пилота. Последняя рамка: как история/текущее состояние/цели становятся действенными в дальнейшем познании без присвоения решений. README — по досье сообщено исправление aa7bc534, другая ссылка b17cdba, неизвестны реальные входы рецензентов. Это НЕ доказанный сбой памяти. Не менять внешние репозитории, не выдавать прошлые статические проверки за новые.

## Контекст и причинное влияние
https://aclanthology.org/2024.tacl-1.9/ — Liu et al., Lost in the Middle (TACL 2024). Открыто fetch+браузер; PDF скачан и текст прочитан /workspace/research_sources/lost.txt. Контролируют позицию документа и размер контекста в QA/key-value; доступность текста в окне не гарантирует применение. Старые модели, не универсальное утверждение о моделях 2026. Query-aware setup улучшает synthetic lookup, мало меняет multi-doc QA; нельзя переносить один тест на способность в целом.

https://arxiv.org/abs/2305.04388 — Turpin et al., Language Models Don't Always Say What They Think (NeurIPS 2023). Открыто fetch+браузер, PDF /workspace/research_sources/faithfulness.txt. Меняли поверхностные bias cues и содержательные weak evidence, объяснения рационализируют сдвиг, не называют воздействие. Вывод: рассказ не доказывает причинного основания; не вывод «все CoT бесполезны/всегда ложны». Для Заучита разделять изменения основания и поверхностных маркеров, одинаковый budget и инструкции, отложенные новые случаи.

## Найденные свежие работы, переданы агенту AI memory для полного чтения
https://arxiv.org/abs/2608.01619 — StateAuditor/VTA: stale stored state can coexist with old policy dependencies. Abstract read. Provenance/chronology ≠ semantic supersession. Controlled STALE gain, negative lifecycle external result. Не обобщать на всю агентную память.
https://arxiv.org/abs/2606.22030 — Nous belief memory: naive Bayesian vs last-write-wins little LoCoMo benefit; better when differing reliable contradictory evidence. Abstract read. Content reliability manipulable, source caps matter.
https://openreview.net/forum?id=2fuMt0utI3 — Operative Contexts: stored vs action-guiding context, silent contextual misalignment. Conceptual desiderata, NOT evaluated integrated architecture. Abstract read.

## Предварительный синтез (наша гипотеза, не установленная теория)
Петля, не одноразовая линейная цепочка: история + модель ситуации + текущая цель -> выбор/извлечение -> проверка актуальности/области/источника -> пересмотр затронутых зависимостей -> кандидат вопроса/подцели -> оценка ценности с учётом затрат/полномочий -> действие/предложение/воздержание -> результат -> обновление сохраняемого состояния. Вопрос может предшествовать извлечению, результат меняет запрос. Установление факта, оценка значимости, изменение цели и разрешение на действие — различные переходы.

Смена LLM меняет не только голос, но интерпретацию и политику; переносится артефактное состояние, функциональная совместимость проверяется отдельно. Информационная новизна не равно полезность; изменение независимо от цели может быть незначимым; старая цель не нынешнее указание. Ошибка — не только retrieval: query formation, source version, stale summary, relevance, conflict handling, generation, persistence. Нужна развилка объяснений на README, не диагноз одного органа.

## Пересмотр зависимостей — не новая проблема
https://dspace.mit.edu/entities/publication/5377b306-4ecc-4687-b1f5-78cbb4a0543a — Jon Doyle, A Truth Maintenance System, 1979. Read institutional repository abstract. Reasons/dependencies maintained, assumptions revised when contradicted, choice of actions linked to reasons. Не доказывает автоматическое извлечение верных зависимостей из естественного языка.
https://plato.stanford.edu/entries/logic-belief-revision/ — прочитаны sections representation/belief bases/iterated change. AGM models formal consistency/minimal-change ideals, logically closed belief sets idealize logical omniscience. Belief bases distinguish independently supported beliefs from derived claims; потеря одной опоры не означает утрату заключения при другой независимой опоре. Факт/оценка/намерение/полномочие нельзя свести к одной операции latest-write-wins.
