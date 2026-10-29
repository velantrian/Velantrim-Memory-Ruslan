# Дополнение: как связать поздний результат с ранними действиями

**Дата:** 29 октября 2026 года  
**Версия:** v1  
**Статус:** исследовательское дополнение; эксперименты не проводились

**Коротко о терминах.** *Временное распределение вклада* (temporal credit assignment) — решение о том, каким ранним действиям приписать часть позднего результата, чтобы учиться на их последствиях. *Eligibility trace* («след доступности») — модельный способ сохранять ранний шаг как кандидата для обновления, пока поздний сигнал ещё может прийти; это не единый доказанный механизм для всех систем.

## Зачем нужен отдельный пробел после аудита

Новый вопрос — может ли система приписать поздний исход более раннему действию внутри многозвенной истории, учитывая задержку, промежуточные события и конкурирующие объяснения. Это не прежний вопрос о том, идут ли сенсорные сигналы из одного источника; не H11 о различении наблюдений и вмешательств; не H2 об объявленной смене правила; не ZD-04 о шуме и смене режима; и не прежние вопросы о повторном проигрывании эпизодов, консолидации или построении маршрутов. Здесь единица анализа — **какое раннее действие меняется после позднего результата**, как долго оно остаётся кандидатом на обновление и не приписывается ли всё по ошибке последнему или самому заметному действию.

## Важные выводы сначала

1. У людей есть узкие, но взаимодополняющие прецеденты: промежуточные состояния могут оцениваться по ожидаемой будущей награде; одно отсроченное вознаграждение может изменить выбор действия, сделанного за два шага до цели; при длинной задержке и промежуточном выборе мозговые представления могут сохранять идентичность причинного выбора до обратной связи [1–3].
2. У животных временное окно зависит от конкретной биологической системы и задачи: у крыс данные о дофаминовых клетках согласуются с долговременной eligibility trace, тогда как в конкретной мышиной задаче NAc поведенчески чувствительное окно было примерно до 1 секунды. Это не универсальная константа и не прямое измерение trace [4–5].
3. В вычислительных системах TD(lambda), expected eligibility traces, RUDDER и TVT показывают разные способы переноса информации назад по истории: через prediction errors, ожидаемых предшественников, декомпозицию возврата или извлечение памяти. Их результаты — свойства моделей и сред, а не доказательства механизма Zauchit [6–9].
4. В рассмотренном наборе прямые данные на физических роботах отсутствуют; AI-результаты относятся к симулированным агентам и игровым/искусственным средам [9–10].

## Данные о людях

### [1] Walsh и Anderson (2011)

**Популяция и система.** 13 студентов Carnegie Mellon University, 18–29 лет, все праворукие, без заявленных неврологических нарушений.  
**Метод и выборка.** Двухрешенческая последовательная задача: первый выбор буквы давал положительный или отрицательный промежуточный cue, второй выбор вёл к вероятностной обратной связи с вероятностями .8/.2. Было 30 тренировочных и два блока по 400 trials; записывались EEG/ERP и сравнивались Q-learning, SARSA и actor–critic с/без eligibility traces.  
**Результат.** Feedback-related negativity была больше для неожиданных исходов; промежуточный cue .2 вызывал более отрицательный ERP, чем .8, хотя сам cue не давал награды. Временной профиль и распределение по скальпу были совместимы с fERN. Модели и симуляции согласовывались с TD reinforcement learning; actor–critic без eligibility traces обычно подходил хуже, тогда как Q-learning и SARSA были конкурентны.  
**Ограничения.** Малый однородный sample, одна короткая лабораторная задача; ERP не является уникальным маркером eligibility trace и может отражать anticipatory affect, conflict или event probability. EEG не локализует источник и не устанавливает причинность; модельный fit не доказывает конкретный биологический алгоритм.  
**Ценность для Zauchit.** Даёт осторожный human precedent: промежуточное состояние можно оценивать по будущей награде, а поведение и event/intermediate-state signals можно анализировать совместно. Это не результат о Zauchit и не свидетельство сознания или субъективного опыта.

### [2] Lehmann и соавт. (2019)

**Популяция и система.** Участники EPFL: clip-art n=12, sound n=15, spatial n=22; отдельный no-reward control: 10, 9 и 12 соответственно. Компьютерная шестисостоянийная задача; pupil diameter записывался в sound и clip-art условиях и отдельным eye tracker в spatial.  
**Метод и выборка.** В первом эпизоде последовательность S–D2–D1–G давала одну отсроченную награду; во втором проверялось повторение подкреплённого действия в D1 и D2. D1 — шаг за один переход до цели, D2 — за два. Среднее число эпизодов: 25.1 в условии с картинками, 19.4 со звуками и 48.1 с пространственными сигналами. Сравнивались модели обучения с eligibility trace и без него; был контроль без награды.
**Результат.** После одной rewarded sequence действие в D2, ведущее к цели, выбиралось в 85% случаев, выше chance 50% (p<0.001), во всех трёх сенсорных условиях; D1 также демонстрировал learning-related bias. Q-lambda лучше объяснял поведение среди сравнённых моделей. В no-reward control повторение D2 составило 56% и было незначимым (p=0.45). Pupil responses менялись вместе с reward-related RL quantities.  
**Ограничения.** Короткая искусственная задача и студенческие выборки; малые modality-specific samples. Результат совместим с широким классом trace-моделей, но не идентифицирует уникальную реализацию; интервалы не варьировались систематически, поэтому exponential time decay нельзя отделить от event-triggered decay. Pupil не является специфичным readout value или prediction error.  
**Ценность для Zauchit.** Прямой human precedent для различения D1 и D2: отсроченный исход может изменить действие, сделанное не только непосредственно перед наградой. Это мотивирует отдельные tests credit-span, delay, intervening-event sensitivity и over-crediting последнего действия; результат не переносится на Zauchit автоматически.

### [3] Witkowski и соавт. (2025)

**Популяция и система.** 20 взрослых около University College London, 11 женщин, средний возраст 23.5 года; без заявленных неврологических или психиатрических нарушений.  
**Метод и выборка.** 3-T fMRI в вероятностной задаче abstract-shape/gift-card learning. В direct trials исход относился к последнему выбору; в indirect trials — к предыдущему выбору после промежуточного решения. В первых двух scanning runs было по 37 direct и 37 indirect trials в каждом; применялись multivoxel/searchlight decoding и ROI-анализы.  
**Результат.** lOFC и hippocampus кодировали идентичность causal choice при feedback даже после длинной задержки и промежуточного решения. В indirect condition lFPC сохраняла pending representation предыдущего причинного выбора; fidelity этой репрезентации предсказывала последующую fidelity causal-choice representation в lOFC и hippocampus. Whole-brain searchlight также указывал на другие фронтальные области, включая medial OFC/vmPFC.  
**Ограничения.** N=20, искусственная явно инструктированная задача и вероятностные gift-card contingencies. BOLD косвенный и медленный; связи между областями не доказывают нейронную причинность. Работа не решает более широкую causal ambiguity реальных ситуаций и не проверяет Zauchit.  
**Ценность для Zauchit.** Мотивирует проверять, сохраняет ли система конкретное раннее действие как pending candidate across intervening decisions, а затем связывает поздний исход именно с ним, а не только с последним salient action.

## Данные на животных

### [4] Pan и соавт. (2005)

**Популяция и система.** 24 фармакологически подтверждённых dopamine neurons, записанных у 11 самцов Wistar rats; всего хирургически использовались 53 крысы. Клетки находились в substantia nigra pars compacta и ventral tegmental area.  
**Метод и выборка.** Chronic extracellular single-unit electrophysiology при classical tone/house-light–saccharin conditioning; применялись random-reward, cued-reward, reward-omission и second-cue-omission trials. Проводилась TD-модель с перебором learning rate alpha и eligibility-decay lambda.  
**Результат.** Ответы клеток на predictive cues возникали быстро; постепенной миграции latency не было. При двух cues клетки отвечали на второй cue и сохраняли этот ответ. При раннем обучении ответ на предсказанную награду сохранялся после развития cue response; после длительного обучения мог исчезать, а при неожиданном пропуске второго cue возвращался. Omitted reward дал значимое снижение population firing (modulation index −0.21±0.20; p<0.01; n=11). TD simulations воспроизводили сосуществование cue и reward responses при высоком lambda и низком alpha (пример lambda=.9, alpha=.005).  
**Ограничения.** Небольшой dataset, presumed dopamine neurons по электрофизиологическим/фармакологическим критериям, а не molecular identity. Вывод о trace опирается на модельные параметры, не на прямое измерение trace; параметры зависят от структуры модели и representation. Задача — простое cue–saccharin conditioning, не многозвенные инструментальные действия.  
**Ценность для Zauchit.** Поддерживает осторожный механизм: раннее predictive event может оставаться eligible для последующего reward update, а cue learning не обязано немедленно стирать reward response. Это не доказывает trace у Zauchit и не даёт оснований выводить сознание или субъективный опыт.

### [5] Yamaguchi и соавт. (2022)

**Популяция и система.** Самцы мышей B6J, 2–4 месяца, head-fixed и water-restricted, в Pavlovian tone/water licking conditioning; система — NAc, включая D1/CaMKII-related signaling и BLA glutamatergic input.  
**Метод и выборка.** 0.5-секундный тон и 2-µL 5% glucose-water; 180 paired и 20 CS-only trials. CS–US delays: −1, −0.5, 0, +0.5, +1, +2 s; группы n=5, 5, 5, 7, 11, 7. Дополнительно NAc AIP control n=7/AIP n=6, D1 antagonist n=5 на группу, mPFC AIP; отдельное optogenetic BLA-to-NAc conditioning.  
**Результат.** Anticipatory licking обучалась при воде в 0, +0.5 или +1 s, но не при −1, −0.5 или +2 s; reported reward-sensitive window был в пределах 1 s. NAc AIP и D1 antagonism нарушали conditioning; mPFC AIP не нарушал. Optogenetic CS также обучался в ChR2, но не Venus control, и зависел от D1.  
**Ограничения.** Малый sex-limited sample, head-fixed Pavlovian task; trace напрямую не записывался. Optogenetic stimulation — искусственный proxy; D1 blockade частично затрагивал US/motor components. Были exclusions из-за expression, отсутствие blinding и between-subject delay groups. Окно 1 s не универсальная биологическая константа.  
**Ценность для Zauchit.** Узкий animal benchmark для проверки delay sensitivity и отличия короткого reward-sensitive окна от более длительного action-history credit. Нельзя заключать, что Zauchit должен иметь trace в 1 s или мышиную схему.

## Вычислительные модели

### [6] Sutton (1988)

**Система и метод.** Численный prediction learner; формальные доказательства и random-walk simulations, без biological sample. Использовались 100 training sets по 10 sequences, repeated- и single-presentation режимы, lambda 0–1 и разные learning rates; metric — RMS error против ideal predictions.  
**Результат.** TD methods обновляют prediction по разностям последовательных predictions, не ожидая финального исхода. Для restricted special cases доказаны convergence/optimality. В random walk TD(lambda<1) имел меньшую reported RMS error, чем lambda=1 Widrow–Hoff; при repeated presentations лучшим был lambda=0, а после одной presentation — примерно lambda=.3 при подходящем learning rate.  
**Ограничения.** Искусственная prediction setting, не action selection и не causal responsibility. Выводы зависят от representation, lambda, learning rate и режима обучения; real-world claims не универсальны.  
**Ценность для Zauchit.** Базовая вычислительная нулевая линия: сравнить terminal-only update с intermediate prediction-error updates и измерить, какие ранние действия меняются при delay/intervening events. Это не результат о Zauchit.

### [7] van Hasselt и соавт. (2021)

**Система и метод.** Expected eligibility traces (ET) и ET(lambda,eta) в stochastic grid world, tabular/linear multi-chain environments и deep agents на Pong и Ms. Pac-Man. Multi-chain: m от 1 до 128, 1,024 episodes, 10 random seeds; linear chains length 16; Atari results — 10 seeds.  
**Результат.** ET имел меньшую prediction error, чем TD(lambda), лучше масштабировался с числом параллельных chains и был особенно полезен при высоком lambda. В Atari QET(lambda=0) ускорял обучение против accumulating-trace Q(lambda=1) на Pong и Ms. Pac-Man. Теория связывает exact ET с expected update instantaneous traces при не большей conditional variance при Markov assumptions.  
**Ограничения.** Synthetic environments и только две Atari games; не state-of-the-art comparison. Гарантии требуют Markov/linear assumptions; nonlinear changing representations остаются проблемой. Это не доказательство истинной causal responsibility и не evidence о Zauchit.  
**Ценность для Zauchit.** Мотивирует сравнивать trajectory trace с expectation-based credit plausible predecessor states/actions и отдельно измерять error/variance при неоднозначной истории.

### [8] Pignatelli и соавт. (2024 revision/publication record)

**Система и метод.** Survey temporal credit assignment in deep RL; новых участников, dataset или обученных агентов в самой работе нет. Формализуются delayed effects, transpositions, low action influence и семейства методов: time heuristics, return decomposition, goal conditioning, sequence-transition modeling, backward planning/learning и meta-learned proxies.  
**Результат.** Работа предлагает taxonomy, единый формализм и диагностические/evaluation protocols; новых causal или behavioral effects не сообщает.  
**Ограничения.** Вторичный источник; выводы зависят от охваченной литературы и formal choices. OpenReview фиксирует reviewer-raised technical/clarity issues, исправленные в revision. Publication wording здесь оставляется осторожным: официальный OpenReview record содержит camera-ready и TMLR decision context.  
**Ценность для Zauchit.** Полезна как рамка дизайна: варьировать delay, intervening events, action influence и sequence structure; измерять over-crediting последнего salient action. Не является результатом о Zauchit.

## ИИ-агенты и робототехника

В рассмотренной подборке нет прямых данных о физических роботах: источники ниже описывают ИИ-агентов в симуляциях, игровых и искусственных средах. Поэтому из них нельзя делать вывод о переносе на реальные робототехнические системы.

### [9] Arjona-Medina и соавт. (2019)

**Система и метод.** RUDDER — computational RL в трёх искусственных delayed-reward задачах и 52 Atari games; сравнения с MC, TD(lambda), MCTS, SARSA(lambda) и reward shaping. Atari: 200M frames/game, 3 random seeds, 10 trials each.  
**Результат.** На трёх artificial tasks RUDDER significantly outperformed comparisons: p<10^-12, p<10^-8 и p<10^-17; speed-ups описаны как exponential с ростом delay. В 52 games быстрее учился в 32 против 20 games baseline; higher average last-10-game scores в 29 против 23. В отдельных games: Bowling 192 vs 56, Solaris 1,827 vs 616, Venture 1,350 vs 820, Seaquest 4,770 vs 1,616.  
**Ограничения.** Метод может быть неэффективен без delayed rewards; LSTM плохо справляется с extremely long sequences; reward redistribution может создавать spurious signals. Это simulated benchmarks, не biological learning, physical robots или Zauchit; gains зависят от baseline и settings.  
**Ценность для Zauchit.** Конкретный computational analogue: проверить, можно ли перераспределить поздний return к ранним decision steps, одновременно тестируя spurious attribution и long-sequence failure.

### [10] Hung и соавт. (2019)

**Система и метод.** Temporal Value Transport (TVT) для Reconstructive Memory Agent в simulated episodic RL. Сравнивались RMA, LSTM+Mem и LSTM; relevant curves имели пять independent training runs, optimization — 384 worker threads; отдельные analyses включали 10, 20 и 50 episodes/trials.  
**Результат.** В Active Visual Match baseline RMA, LSTM и LSTM+Mem не учились в principal distractor-reward setting, тогда как TVT учился искать и возвращать relevant cue и улучшал P3. В Latent Information Acquisition только TVT решал задачу; non-TVT agents в среднем набирали 15 points, RMA трогал примерно один object. В Passive Visual Match RMA извлекал memory через 30-секундный distractor, но эта задача сама по себе не требовала long-term credit assignment.  
**Ограничения.** TVT назван heuristic; value transport может bias и ухудшать short-term credit; в Montezuma’s Revenge он не trigger-ился. Задачи contrived, результаты не доказывают human-like memory, causal learning, physical-robot competence или Zauchit mechanism.  
**Ценность для Zauchit.** Даёт измеримый pattern для proposed test: retrieval of an earlier event должен усиливать credit позднего outcome к раннему действию, но нужно отдельно проверять, не создаёт ли retrieval ложную attribution.

## Новые гипотезы

Все гипотезы ниже **PROPOSED / NOT RUN**. Ни один эксперимент не проводился. Размеры выборки, величины эффектов и критерии должны быть preregistered до запуска.

### DCA-01 — Как далеко переносится обучение

**Prediction.** После одного позднего исхода изменение выбора будет у раннего causal action (например, D2), а не только у непосредственно предшествующего D1; эффект D2 сохранится при одном нейтральном intervening action и ослабнет при двух.  
**Контроль.** No-reward control; reward, привязанный к D1; reward, привязанный к D2; matched last-action repetition control.  
**Метрики.** ΔP выбора D2 и D1 после исхода, credit-span slope по числу intervening steps, terminal prediction error, частота last-action over-crediting.  
**Фальсификация/решение.** Гипотеза поддерживается только если preregistered D2 effect превышает no-reward и last-action controls, а effect-by-distance имеет заранее заданное монотонное ослабление. Она опровергается, если только D1 меняется либо D2 не отличается от no-reward control.

### DCA-02 — Сохранённый ранний выбор или простая заметность

**Prediction.** Если раннее действие извлекается из памяти непосредственно перед поздним исходом, credit раннего действия увеличивается; простое усиление perceptual salience без retrieval не даёт того же паттерна.  
**Контроль.** Retrieval cue, не связанный с causal action; salience-matched cue; scrambling cue–action identity; direct-outcome condition без intervening decision.  
**Метрики.** Credit allocation к раннему шагу, retrieval accuracy, latency/ошибки выбора, calibration между predicted и actual outcome, interaction retrieval × causal identity.  
**Фальсификация/решение.** Поддержка требует заранее заданного interaction retrieval × causal identity и отсутствия эквивалентного эффекта в salience control. Если любой salient cue одинаково переносит credit на недавнее действие, гипотеза о pending-specific mechanism фальсифицируется.

### DCA-03 — Различить задержку по времени и число промежуточных событий

**Prediction.** Поведение будет зависеть от задержки нелинейно: короткая задержка поддержит ранний credit, а достаточно длинная задержка или дополнительные нейтральные события его снизят; форма кривой будет отличаться для outcome-only update и trace-like model.  
**Контроль.** Фиксированная wall-clock delay с разным числом событий; разное wall-clock delay при одинаковом числе событий; no-reward; reward-predictive cue без финального исхода.  
**Метрики.** Кривая ΔP раннего действия по delay и event count, model comparison TD(0)/TD(lambda)/return redistribution, calibration, false-credit rate к distractor actions.  
**Фальсификация/решение.** Нужна preregistered superiority одной модели по held-out prediction и заранее заданный delay/event interaction. Гипотеза не подтверждается, если credit не меняется с delay/event count или если сложная trace-модель не превосходит terminal-only baseline вне обучающей выборки.

## Итоговая осторожность

Совокупность источников делает delayed temporal credit assignment самостоятельным и операционализируемым пробелом, но не устанавливает механизм Zauchit. Биологические, human, computational и AI evidence нельзя смешивать; ни один источник не доказывает сознание или субъективный опыт. Все proposed effects и decisions о sample size требуют preregistration. На момент этой версии эксперименты не запускались.

## References

1. Walsh, M. M., & Anderson, J. R. (2011). *Learning from delayed feedback: neural responses in temporal credit assignment*. Cognition, Affective & Behavioral Neuroscience, 11(2), 131–143. https://doi.org/10.3758/s13415-011-0027-0
2. Lehmann, M. P., Xu, H. A., Liakoni, V., Herzog, M. H., Gerstner, W., & Preuschoff, K. (2019). *One-shot learning and behavioral eligibility traces in sequential decision making*. eLife, 8, e47463. https://doi.org/10.7554/eLife.47463
3. Witkowski, P. P., Rondot, L. J. H., Kurth-Nelson, Z., Garvert, M. M., Dolan, R. J., & Behrens, T. E. J. (2025). *Neural mechanisms of credit assignment for delayed outcomes during contingent learning*. eLife, 101841. https://doi.org/10.7554/eLife.101841
4. Pan, W.-X., Schmidt, R., Wickens, J. R., & Hyland, B. I. (2005). *Dopamine Cells Respond to Predicted Events during Classical Conditioning: Evidence for Eligibility Traces in the Reward-Learning Network*. Journal of Neuroscience, 25(26), 6235–6242. https://doi.org/10.1523/JNEUROSCI.1478-05.2005
5. Yamaguchi, K., Maeda, Y., Sawada, T., Iino, Y., Tajiri, M., Nakazato, R., Ishii, S., Kasai, H., & Yagishita, S. (2022). *A behavioural correlate of the synaptic eligibility trace in the nucleus accumbens*. Scientific Reports, 12, 1921. https://doi.org/10.1038/s41598-022-05637-6
6. Sutton, R. S. (1988). *Learning to Predict by the Methods of Temporal Differences*. Machine Learning, 3, 9–44. https://doi.org/10.1007/BF00115009
7. van Hasselt, H., Madjiheurem, S., Hessel, M., Silver, D., Barreto, A., & Borsa, D. (2021). *Expected Eligibility Traces*. Proceedings of the AAAI Conference on Artificial Intelligence, 35(11), 9997–10005. https://doi.org/10.1609/aaai.v35i11.17200
8. Pignatelli, E., Ferret, J., Geist, M., Mesnard, T., van Hasselt, H., Pietquin, O., & Toni, L. (2024 revision/publication record). *A Survey of Temporal Credit Assignment in Deep Reinforcement Learning*. OpenReview. https://openreview.net/forum?id=bNtr6SLgZf
9. Arjona-Medina, J. A., Gillhofer, M., Widrich, M., Unterthiner, T., Brandstetter, J., & Hochreiter, S. (2019). *RUDDER: Return Decomposition for Delayed Rewards*. Advances in Neural Information Processing Systems 32. https://proceedings.neurips.cc/paper/2019/hash/16105fb9cc614fc29e1bda00dab60d41-Abstract.html
10. Hung, C.-C., Lillicrap, T., Abramson, J., Wu, Y., Mirza, M., Carnevale, F., Ahuja, A., & Wayne, G. (2019). *Optimizing Agent Behavior over Long Time Scales by Transporting Value*. Nature Communications, 10, 5223. https://doi.org/10.1038/s41467-019-13073-w
