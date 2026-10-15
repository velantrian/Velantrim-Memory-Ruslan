# Анализ SELF-EXP-01 «Self, Experience and Consciousness» · 2026-10-15

Статус: аналитическая заметка. Оригинальный файл `projects/self-experience-consciousness.md` не изменён. Не канон, не пререгистрация, не результат.

## Вывод
Как архив и граница допустимых утверждений документ аккуратный. Как эксперимент он пока пуст.

- «Я» нигде не операционализировано: фактически измеряется только метакогнитивная калибровка (знает ли система свои ошибки).
- Нет метрик, порогов, размера выборки; «holdout», «leakage check», «independent assessment» не определены.
- Единственная гипотеза SELF-CAUSAL-01 не отличает «модель себя» от «просто больше информации»: условие C даёт больше информации, чем A и B. Нужен контроль C′ (та же проверенная информация о задачах без самоописания) и проверка порчей подстановкой.
- Возможная утечка ответов между условиями.
- Метки A/B/C значат разное в SYN-01, SELF-CAUSAL-01, CURRENT.md и копии в Notion.
- Унаследована ошибка ссылок v1.1.1: «Мне нравится B → UNSELECTED», «Возможно, выберу A → UNSELECTED».
- Антропоморфный риск в названии; эксперименты 5 и 6 пересекаются с CTX-REVISION и EXP-C.

## Пять предложенных простых компьютерных тестов
1. **T1 — калибровка своих способностей:** система заранее предсказывает, где ошибётся, затем сверка с фактом.
2. **T2 — свои и чужие действия:** атрибуция изменений состояния себе или внешнему источнику.
3. **T3 — реестр от первого лица:** высказывания «Я выбираю / нравится / ещё не выбрал» с исправленными эталонами (UNKNOWN ≠ UNSELECTED).
4. **T4 — «где я»:** граница системы и происхождение данных, без утверждений о сознании.
5. **T5 — непрерывность:** канареечный токен, переживающий смену сессии.

## Приоритеты
- P0: определить «Я» через измеримое поведение; добавить контроль C′; унифицировать метки A/B/C; исправить эталоны v1.1.1 → v1.1.2.
- P1: метрики, пороги, размер выборки, определения holdout/leakage.
- P2: T4, T5; развести эксперименты 5–6 с CTX-REVISION и EXP-C.


## 2026-10-15 — Local synthetic pilot evidence addendum

**Source and scope.** Summarized from the user-provided `Existing Synthetic Pilot Evidence and Negative Results` and `VELANTRIM-SELF-EXP-01 — Experiment Passports EXP-01–EXP-12`; this patch does not rerun or independently reproduce the pilots. The reports describe four local pure-Python v1.1 toy pilots (EXP-01/02/03/08); eight passports remain design-only. No LLM/API, human/animal, network, Velantrim runtime, or project code was involved. These are not INIT-01, CREAT-INIT-01, Family C, or SYN-01 results, and do not create a new experiment ID.

- **EXP-01 / ISO-PILOT-01:** holdout accuracy 71.39% versus 66.81% no-model and 66.92% static profile; all seven programmed criteria passed. Ordinary Bayesian calibration in the toy generator explains the result.
- **EXP-02 / ISO-PILOT-02:** opposite-history policies disagreed on 98.33% of decisions; same-history twins agreed 100%. Reset/swap/restore matched programmed outcomes. Recorded deviation: holdout context order was fixed alternating, not randomized as preregistered.
- **EXP-03 / ISO-PILOT-03:** the hand-coded signature comparator reached 90.79% accuracy versus 57.79% temporal-only, with false-self rates of 8.74% versus 70.16%. The classifier encoded the generator's rule; logged delays were unused and the planned low-confound arm was absent.
- **EXP-08 / ISO-PILOT-04:** raw-surprise control exceeded fixed ε=.15 by +0.03480 net reward but underperformed greedy by −0.05915 and signal-ablation by −0.01939; it adapted 5.805 steps more slowly than greedy. The report says the full preregistered H1 was not supported, H3 was false, and greedy performed best in these worlds.

**Inference ceiling.** EXP-01–03 pass only narrow code-defined checks with ordinary algorithmic explanations. EXP-08 is negative evidence against this raw-surprise rule, not all uncertainty or regulatory mechanisms. None measures phenomenal experience (P), consciousness, mineness, or felt emotion. The four pilots do not change SELF-CAUSAL-01 status (proposed / not run). The most actionable functional gap remains tested outcome-grounded state revision and transfer to novel choices under matched retrieval/context; endogenous question formation is separate. The source reports identify local raw records and preregistration; this patch is a summary, not a raw-data archive.
