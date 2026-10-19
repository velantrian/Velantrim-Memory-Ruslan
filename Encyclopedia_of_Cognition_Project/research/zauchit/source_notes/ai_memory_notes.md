# Исследовательские заметки: память, меняющая будущие решения

Дата исследования: 2026-10-18. Прочитаны сами первичные страницы arXiv (HTML/abstract), а не только сниппеты.

## 1. Generative Agents
URL: https://arxiv.org/html/2304.03442v2
Механизм: поток долговременных естественно-языковых наблюдений; retrieval по смеси релевантности, давности и важности; периодическая рефлексия, синтезирующая более высокоуровневые выводы; планирование, которое рекурсивно раскладывается в действия. Рефлексии и планы снова попадают в поток памяти и потому могут менять дальнейшие действия.
Тесты: 25 агентов в sandbox Smallville на два игровых дня; controlled interview по self-knowledge, memory, plans, reactions, reflections; end-to-end социальная симуляция и party seed. 100 участников сравнивали полный агент, три абляции и human-authored ответы within-subject. Каждая из памяти наблюдений, рефлексии и планирования была критична.
Что доказано: устойчивое поведение и причинный вклад компонентов в этой узкой симуляции; агенты распространили приглашение и пришли на вечеринку по одному seed.
Ограничения/ошибки: эксперименты не измеряют обучение параметров или перенос в новые домены; абляции используют один и тот же накопленный поток, что консервативно, но не является полностью независимым переигрыванием. Типичные ошибки: не извлечена нужная память, выдуманы детали, чрезмерно формальная речь.

## 2. Reflexion
URL: https://arxiv.org/html/2303.11366
Механизм: Actor действует; Evaluator возвращает scalar reward; Self-Reflection превращает trajectory + reward в текстовую причинную/тактическую подсказку; она складывается в episodic long-term memory (обычно последние 1–3 опыта) и подаётся Actor на следующую попытку. Это меняет последующее решение без обновления весов.
Тесты: AlfWorld (134 окружения), HotPotQA, HumanEval/MBPP и LeetcodeHard; сравнения с ReAct, CoT, episodic-memory абляцией. Результаты в статье: +22% на AlfWorld, +20% HotPotQA, +11% HumanEval против сильных baseline. На HotPotQA self-reflection дала +8 процентных пунктов сверх преимущества простой episodic memory; CoT/ ReAct-only не улучшались вероятностно между попытками.
Что доказано: feedback, преобразованный в явное объяснение ошибки, может менять стратегию на следующей попытке.
Ограничения/отрицательный перенос: reward/evaluator task-specific, память обрезается до 3; система учится главным образом на текущей траектории, может закрепить ошибочную рефлексию; нет теста долгого накопления конфликтующих правил. Для code task авторы отдельно предупреждают о рисках автономного выполнения непроверенного кода.

## 3. MemGPT
URL: https://arxiv.org/html/2310.08560
Механизм: OS-inspired virtual context. Main context содержит system instructions, working context, FIFO; внешние recall/archival stores — не видимы без явного paging. LLM сам вызывает функции для записи, eviction, retrieval и heartbeat-цепочек; при переполнении очередь суммируется и вытесняется, а старые сообщения остаются в recall storage.
Тесты: document analysis с файлами длиннее окна и multi-session chat; сравнение с базовыми fixed-context/long-context подходами. Заявлено превосходство в обеих областях и способность помнить, отражать и эволюционировать в многосессионном чате.
Что доказано: управляемое paging расширяет доступный контекст; это в первую очередь управление доступом к истории, а не доказательство формирования новых устойчивых убеждений.
Ограничения: self-directed retrieval зависит от способности модели правильно решить, что выгрузить/достать; summary может потерять или исказить детали; результаты ранней системы и зависят от function-calling, prompt и конкретных моделей. Плохой retrieval является источником ошибок, даже при наличии записи.

## 4. A-MEM
URL: https://arxiv.org/html/2502.12110
Механизм: каждая новая интеракция превращается LLM в атомарную заметку с исходным содержанием, timestamp, keywords, tags, contextual description и embedding. Новая заметка ищет соседей, LLM решает, какие связи создать; соседние заметки могут эволюционировать (обновление контекста/тегов). Retrieval возвращает релевантные заметки и связанные «box» узлы.
Тесты: LoCoMo (около 9K токенов, до 35 сессий, 7,512 QA) и DialSim; пять типов вопросов LoCoMo: single/multi-hop, temporal, open-domain, adversarial. Сравнения с memory baselines показывают улучшение, но метрики зависят от LLM-generated annotations и embedding retrieval.
Что доказано: память меняется структурно при поступлении новых фактов, а не только хранит журнал; это правдоподобный механизм контекстного влияния на будущий retrieval.
Ограничения/риски: keywords/descriptions/links генерирует та же модель, поэтому ошибки и ложные причинные связи могут самоукрепляться; evolving note может переписать старое; benchmark в основном QA/retrieval, не реальное действие и не доказательство устойчивого поведения.

## 5. LoCoMo
URL: https://arxiv.org/html/2402.17753v1
Роль: первичный benchmark, а не memory architecture. Диалоги синтетически построены из persona и temporal event graph, около 300 turns/9K tokens, до 35 sessions. QA включает single-hop, multi-hop, temporal, open-domain и adversarial/unanswerable; event summarization оценивается FactScore precision/recall; также multimodal dialogue generation.
Контролируемые сравнения: constrained base models (Mistral-7B, Llama-70B, GPT-3.5/4), GPT-3.5-16K, RAG по dialogue/observations/summaries. Overall F1 для GPT-3.5 4K 22.4, 16K 37.8; RAG observations top-5 41.4, summary top-10 31.5, dialog top-25 35.8 (категории неоднородны). Adversarial вопросы особенно ломают уверенное угадывание.
Вывод: наличие длинного окна не равно умению использовать историю; извлечение и синтез расходятся. Ограничения: синтетические разговоры/автоматизированная генерация, F1 и FactScore не измеряют полезность действия или долговременный перенос.

## 6. LongMemEval
URL: https://arxiv.org/html/2410.10813v1
Роль: benchmark для ассистентской памяти. 500 human-curated вопросов, пять способностей: information extraction, multi-session reasoning, knowledge updates, temporal reasoning, abstention. Истории timestamped, evidence спрятаны в естественных task-oriented диалогах; LongMemEvalS около 115K токенов, M — 500 сессий/около 1.5M токенов.
Результаты: long-context LLM теряли примерно 30–60% производительности на S; GPT-4o в более простом режиме показывал лишь 30–70% accuracy. Важны обновления фактов (старое не должно переехать в новое) и отказ от ответа при неизвестном.
Вывод: настоящая memory competence — не только recall, но и versioning, temporal grounding и abstention.
Ограничения: evidence sessions LLM-simulated, затем human-edited; тест всё ещё вопрос-ответ, не автономное планирование. Бенчмарк показывает трудность, но не гарантирует, что улучшение score означает безопасное поведение.

## 7. CLIN
URL: https://arxiv.org/html/2310.10134
Механизм: persistent meta-memory причинных абстракций «necessary»/«does not contribute», извлечённых из собственных траекторий и refinement между trial; controller формирует цель перед действием. Сравнивается с Reflexion, который фокусируется на ошибках текущего trial.
Тесты: ScienceWorld, последовательная адаптация, новые окружения и задачи; base, Gen-Env, Gen-Task, G+A. Средний score CLIN: 48.6 Base, 52.7 Gen-Env, 69.5 G+A; против Reflexion 39.4 overall в приведённой таблице. Ablation свободной (неструктурированной) памяти даёт падение 6.2, controller — 18.1.
Что доказано: структурированные причинные обобщения могут переносить опыт на новые варианты; эффект сильнее на длинных задачах.
Ограничения/отрицательный перенос: агент учится только на том, что сам исследовал; невыбранные действия не становятся знаниями. Авторы показывают poor retrieval: обобщение про stove извлекается вместо нужного oven/blast furnace, и агент повторяет ошибку. Вредные и полезные causal learnings накапливаются вместе.

## Сводный критерий для проекта
Сильное свидетельство «история меняет будущие решения» требует: (а) решение после опыта отличается от baseline; (б) есть контролируемая память/рефлексия-абляция; (в) улучшение переносится на новые эпизоды, а не только на повторный ответ; (г) измерены обновление, abstention и ошибки retrieval. Generative Agents, Reflexion и CLIN дают наиболее прямые causal/behavioral данные. MemGPT и A-MEM показывают архитектурные способы изменения доступного контекста/структуры, но не равны доказательству устойчивого обучения. LoCoMo и LongMemEval показывают, что recall, temporal updates и отказ — отдельные трудные способности.
Для более широкой цели «продолженная познавательная деятельность» результаты пока не свидетельствуют о сознании. Они показывают инженерные циклы накопления, отбора, абстракции и коррекции, причём право постановки целей и решений владельца должно оставаться у человека: память может предлагать релевантный вклад, но не присваивать авторство или полномочия.

## 8. STALE / StateAuditor
URL: https://arxiv.org/abs/2608.01619
Механизм: benchmark для implicit policy adaptation gap (IPA): сохранённое состояние уже устарело, но draft/план всё ещё зависит от старого значения. StateAuditor идёт от stored state к draft: LLM предлагает old-to-new transitions, deterministic code привязывает каждую цитату к одной записи и проверяет provenance/chronology. Это намеренно не проверка semantic supersession.
Тесты: 400 STALE сценариев, 50-сессионные истории, один независимый ответ на query. Strict single-query VTA 0.736 против 0.686 locked predecessor, +5.0 пункта, 95% CI [+2.9,+7.2]; независимый judge 0.738 против 0.680. Матched control с теми же evidence, adapter и call budget — 0.692 (+0.6, n.s.), то есть эффект связан с transition machinery, а не объёмом контекста/числом вызовов.
Отрицательный результат: на независимом HorizonBench draft-side audit дал большую часть внешнего выигрыша; на более сложном authored lifecycle set выигрыш исчез, хотя false invalidation оставалась контролируемой. Авторы не заявляют general-purpose agent memory.

## 9. Nous: reliability-conditioned belief updating
URL: https://arxiv.org/abs/2606.22030
Механизм: entity-attribute представляется categorical probability distribution; closed-form Bayesian update, surprise для revision, entropy-based forgetting. Reliability-conditioned variant оценивает надёжность по epistemic language; provenance-capped variant ограничивает доверие источником.
Тесты: controlled ablation на LoCoMo, contradiction benchmark с разной надёжностью источников, memory-poisoning tests. Bayesian updating почти не помогает против last-write-wins на обычном LoCoMo, где мало конфликтов; существенно выигрывает на conflicting evidence. Provenance cap сопротивляется volumetric poisoning, но требует implementation trade-offs.
Ограничения: текстовая reliability уязвима манипуляции; строгий token-F1 и LLM-as-judge на одинаковых outputs расходятся на 27.5 пункта.

## 10. Operative Contexts
URL: https://openreview.net/forum?id=2fuMt0utI3
Концептуальный первичный источник: различает stored memory и operative context — факты, реально направляющие действие. Silent contextual misalignment — скрытое действие из неуместного контекста. Предлагаемые stress tests: conflict revision, scope control, task-demand selection, uncertainty preservation. Это полезная рамка для проверки, дошло ли обновление памяти до поведения.
