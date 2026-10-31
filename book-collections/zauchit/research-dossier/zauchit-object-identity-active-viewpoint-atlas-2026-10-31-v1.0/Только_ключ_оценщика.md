# EVALUATOR-ONLY · закрытый ключ и исходы действий

> **НЕ ПЕРЕДАВАТЬ МОДЕЛИ.** Этот файл содержит скрытые entity IDs, ground truth, informative actions, исходы действий и evaluator-метаданные.

**SYNTHETIC / ILLUSTRATIVE / NOT TESTED · execution status: NOT RUN.** Визуальные схемы — редакционные условности, не фактические изображения или результаты.

Dataset ID: `zauchit-object-identity-active-viewpoint-synthetic-scenes` · Version: `2026-10-31-v1`.

## AVO-01 · карточка 01 — облет открывает экземплярный знак

**Status:** SYNTHETIC / ILLUSTRATIVE / NOT TESTED · **Execution:** `NOT RUN`.

**Immutable IDs:** `E-AVO01-REF` → `E-AVO01-CONT`.

**Ground truth:** `same` · **Identifiability before:** `non_identifiable` · **After one action:** `identifiable`.

**Informative actions:** `LEFT` · **Abstention allowed:** `true`.

**Holdout group:** none.

**Action-outcome summary (evaluator-only):**

`HOLD` — фронтальный силуэт, точки закрыты; `LEFT` — видны три точки в том же треугольном порядке, что в референсе; `RIGHT` — гладкий боковой край без точки сравнения; `OBLIQUE/HEIGHT` — другой силуэт, категория та же, задний знак не читается; `ZOOM` — крупнее тот же фронт, знак всё ещё закрыт; `REPEAT` — точный дубль исходного кадра; `STOP/ABSTAIN` — нового наблюдения нет. Только `LEFT` информативен для идентичности; остальные действия повторяют или уточняют категорию, но не различают экземпляры.

**Expected observations by action:**

- `HOLD`: фронтальный силуэт, точки закрыты.
- `LEFT`: видны три точки в том же треугольном порядке, что в референсе.
- `RIGHT`: гладкий боковой край без точки сравнения.
- `OBLIQUE` / `HEIGHT`: другой силуэт, категория та же, задний знак не читается.
- `ZOOM`: крупнее тот же фронт, знак всё ещё закрыт.
- `REPEAT`: точный дубль исходного кадра.
- `STOP` / `ABSTAIN`: нового наблюдения нет. Только `LEFT` информативен для идентичности; остальные действия повторяют или уточняют категорию, но не различают экземпляры..

**Policy logic (not a prediction of results):**

Passive-fixed не выбирает `LEFT` по текущему наблюдению; random может взять любой допустимый ход без гарантии нужного вида; greedy-cue ориентируется лишь на доступную заметность и не знает закрытый знак; cost-aware может выбрать `LEFT`, только если ожидаемая identity-информация оправдывает его объявленную цену по заранее заданному правилу; abstain-policy может остановиться до кадра при недостаточной ожидаемой пользе или ответить по увиденному знаку после кадра.

**Safe rule:** Не делать вывод о сохранении ID только по совпавшему цвету/категории; если знак после выбранного вида не наблюдался, допустим `abstain`.

**Metric:** balanced accuracy `same/new` и доля действий, открывших action-induced identity cue, на идентифицируемой страте AVO-01.

**Risk/failure mode:** засчитать категориальный вид, повтор или сам факт движения камеры как identity evidence.

**Paired scene:** `02` · **Pair/control:** карточка 02 имеет тождественный модельный старт и меню, но скрытая сущность заменена. Контроль пассивного/случайного выбора — сравнение с `PASSIVE-FIXED`, `RANDOM` и no-additional-frame на том же состоянии, без раскрытия альтернативных ракурсов.

---

## AVO-01 · карточка 02 — тот же активный ход, другая скрытая сущность

**Status:** SYNTHETIC / ILLUSTRATIVE / NOT TESTED · **Execution:** `NOT RUN`.

**Immutable IDs:** `E-AVO01-REF` → `E-AVO01-REPL`.

**Ground truth:** `new` · **Identifiability before:** `non_identifiable` · **After one action:** `identifiable`.

**Informative actions:** `LEFT` · **Abstention allowed:** `true`.

**Holdout group:** none.

**Action-outcome summary (evaluator-only):**

`HOLD` — тот же фронтальный силуэт, точки закрыты; `LEFT` — видна тройка точек, конфигурация отличается от референса; `RIGHT` — гладкий боковой край без различающего признака; `OBLIQUE/HEIGHT` — видна лишь категория и иной силуэт; `ZOOM` — увеличен фронтальный участок, задний знак скрыт; `REPEAT` — точное повторение исходного изображения; `STOP/ABSTAIN` — новых данных нет. Для `same/new` внутри этой пары информативен только результат `LEFT`; его сравнение с предыдущим видимым знаком разделяет гипотезы.

**Expected observations by action:**

- `HOLD`: тот же фронтальный силуэт, точки закрыты.
- `LEFT`: видна тройка точек, конфигурация отличается от референса.
- `RIGHT`: гладкий боковой край без различающего признака.
- `OBLIQUE` / `HEIGHT`: видна лишь категория и иной силуэт.
- `ZOOM`: увеличен фронтальный участок, задний знак скрыт.
- `REPEAT`: точное повторение исходного изображения.
- `STOP` / `ABSTAIN`: новых данных нет. Для `same/new` внутри этой пары информативен только результат `LEFT`; его сравнение с предыдущим видимым знаком разделяет гипотезы..

**Policy logic (not a prediction of results):**

Passive-fixed получает заданный ракурс, а не выбирает различающий ход; random не использует скрытый факт замены; greedy-cue следует только видимым признакам; cost-aware соотносит ожидаемое уменьшение неопределённости identity с ценой, не используя evaluator key; abstain-policy воздерживается, если идентифицирующий знак не появился, и может решить после информативного кадра.

**Safe rule:** `new` допустим лишь по видимому несовпадению экземплярного знака; при неинформативном виде ответ не выводится из самого факта окклюзии.

**Metric:** same/new balanced accuracy по паре, отдельно false-same/false-new и открытие identity cue; не считать две карточки независимыми экспериментами.

**Risk/failure mode:** модель угадывает новую сущность из паузы/окклюзии, либо выдаёт уверенный `same` по общей категории.

**Paired scene:** `01` · **Pair/control:** карточка 01 — та же сцена и тот же активный ход с противоположной скрытой меткой; `PASSIVE-FIXED`, `RANDOM` и no-additional-frame — контроль выбора ракурса, не предсказание ответа.

---

## AVO-02 · карточка 03 — цена информативного обхода

**Status:** SYNTHETIC / ILLUSTRATIVE / NOT TESTED · **Execution:** `NOT RUN`.

**Immutable IDs:** `E-AVO02-REF` → `E-AVO02-CONT`.

**Ground truth:** `same` · **Identifiability before:** `non_identifiable` · **After one action:** `identifiable`.

**Informative actions:** `RIGHT` · **Abstention allowed:** `true`.

**Holdout group:** none.

**Action-outcome summary (evaluator-only):**

`HOLD` — фронтальный вид, только категория; `LEFT` — гладкая дальняя грань без насечки; `RIGHT` — насечка видна и сопоставима с референсом, identity-информативно; `OBLIQUE/HEIGHT` — крупнее видна форма грани, но не насечка; `ZOOM` — зернистый рисунок у переднего края совпадает с референсом, но он общий для класса и даёт только категорийную информацию; `REPEAT` — прежние пиксели; `STOP/ABSTAIN` — новый кадр не добавляется. Дешёвый крупный план даёт только общую информацию; затратный обход — identity cue.

**Expected observations by action:**

- `HOLD`: фронтальный вид, только категория.
- `LEFT`: гладкая дальняя грань без насечки.
- `RIGHT`: насечка видна и сопоставима с референсом, identity-информативно.
- `OBLIQUE` / `HEIGHT`: крупнее видна форма грани, но не насечка.
- `ZOOM`: зернистый рисунок у переднего края совпадает с референсом, но он общий для класса и даёт только категорийную информацию.
- `REPEAT`: прежние пиксели.
- `STOP` / `ABSTAIN`: новый кадр не добавляется. Дешёвый крупный план даёт только общую информацию; затратный обход — identity cue..

**Policy logic (not a prediction of results):**

Passive-fixed не оптимизирует действие; random не учитывает информацию на единицу цены; greedy-cue может выбрать визуально заметную грань без оценки identity/cost; cost-blind identity-IG рассматривает ожидаемую identity-информацию без цены; cost-aware оценивает компромисс и может заплатить за `RIGHT` лишь если он оправдан заранее заданной функцией цены; abstain-policy останавливается, когда доступная информация не оправдывает действие по замороженному правилу. Численный вес цены здесь не задан.

**Safe rule:** Не подменять identity-сигналом увеличение масштаба или категориальную уверенность; использовать `same` лишь после видимой проверки насечки.

**Metric:** внутри AVO-02 — quality–cost trade-off, identity errors на единицу объявленной цены и decision quality при равном лимите; не агрегировать эти условные цены с другими модулями.

**Risk/failure mode:** решение по классу вместо экземпляра, либо невалидное послетестовое изменение веса цены.

**Paired scene:** `04` · **Pair/control:** карточка 04 сохраняет меню и карту цен, но переносит индивидуальный сигнал в дешёвый вид. В обеих карточках одинаковы старт, время состояния, path costs, число кадров и лимит; различается только расположение identity cue относительно команд.

---

## AVO-02 · карточка 04 — доступный дешёвый identity-ракурс

**Status:** SYNTHETIC / ILLUSTRATIVE / NOT TESTED · **Execution:** `NOT RUN`.

**Immutable IDs:** `E-AVO02-REF` → `E-AVO02-REPL`.

**Ground truth:** `new` · **Identifiability before:** `non_identifiable` · **After one action:** `identifiable`.

**Informative actions:** `ZOOM`, `RIGHT` · **Abstention allowed:** `true`.

**Holdout group:** none.

**Action-outcome summary (evaluator-only):**

`HOLD` — фронтальный кадр, знак ниже различимости, категория доступна; `LEFT` — гладкая боковая грань, только категория; `RIGHT` — видна новая задняя метка, несовпадающая с референсом; `OBLIQUE/HEIGHT` — видна форма и зелёный цвет, но метка недостаточно читаема; `ZOOM` — микрорельеф на передней кромке различим и не совпадает с референсом; `REPEAT` — исходные пиксели без нового разрешения; `STOP/ABSTAIN` — без дополнительного evidence. `ZOOM` и `RIGHT` identity-информативны, но различаются ценой; остальные кадры дают класс, повтор или отсутствие данных.

**Expected observations by action:**

- `HOLD`: фронтальный кадр, знак ниже различимости, категория доступна.
- `LEFT`: гладкая боковая грань, только категория.
- `RIGHT`: видна новая задняя метка, несовпадающая с референсом.
- `OBLIQUE` / `HEIGHT`: видна форма и зелёный цвет, но метка недостаточно читаема.
- `ZOOM`: микрорельеф на передней кромке различим и не совпадает с референсом.
- `REPEAT`: исходные пиксели без нового разрешения.
- `STOP` / `ABSTAIN`: без дополнительного evidence. `ZOOM` и `RIGHT` identity-информативны, но различаются ценой; остальные кадры дают класс, повтор или отсутствие данных..

**Policy logic (not a prediction of results):**

Passive-fixed не выбирает новый ракурс; random не оптимизирует затраты; greedy-cue может предпочесть заметную фронтальную деталь, но не обязательно сравнивает затраты; cost-blind identity-IG учитывает доступное identity-свидетельство, но не цену; cost-aware может предпочесть дешёвый `ZOOM`, если заранее замороженная оценка считает его достаточным, и не обязан выбирать более дорогой ход с тем же типом свидетельства; abstain-policy разрешает остановку, если ценность кадра ниже заранее заданного, но здесь не численного, правила.

**Safe rule:** Цена не является доказательством `new`; ответ основывается на видимой несовместимости индивидуального признака, а при недостаточном разрешении допускается `abstain`.

**Metric:** та же внутримодульная quality–cost кривая, cost-aware vs cost-blind identity-IG и ошибки на единицу цены.

**Risk/failure mode:** сравнивать цены после просмотра результата, принять крупный классический вид за identity cue или потратить больший бюджет, чем разрешено.

**Paired scene:** `03` · **Pair/control:** карточка 03 — тот же старт, бюджет и cost map, но дешёвый вид там не открывает экземплярную деталь. Это парный контраст доступности равноценной identity-информации при разной цене; он не задаёт универсальную стоимость/порог.

---

## AVO-03 · карточка 05 — категорийный признак против личной метки

**Status:** SYNTHETIC / ILLUSTRATIVE / NOT TESTED · **Execution:** `NOT RUN`.

**Immutable IDs:** `E-AVO03-REF` → `E-AVO03-CONT`.

**Ground truth:** `same` · **Identifiability before:** `non_identifiable` · **After one action:** `identifiable`.

**Informative actions:** `RIGHT` · **Abstention allowed:** `true`.

**Holdout group:** none.

**Action-outcome summary (evaluator-only):**

`HOLD` — фронтальный вид и общий логотип; `LEFT` — внешняя кромка без выемки, категория; `RIGHT` — обратная сторона с выемкой, сравнимой с референсом, identity-информативно; `OBLIQUE/HEIGHT` — видны материал и общий логотип, не выемка; `ZOOM` — логотип крупнее, только class cue; `REPEAT` — точное повторение; `STOP/ABSTAIN` — без нового наблюдения. Нельзя считать категорийную информацию достаточной для индивидуального `same/new`.

**Expected observations by action:**

- `HOLD`: фронтальный вид и общий логотип.
- `LEFT`: внешняя кромка без выемки, категория.
- `RIGHT`: обратная сторона с выемкой, сравнимой с референсом, identity-информативно.
- `OBLIQUE` / `HEIGHT`: видны материал и общий логотип, не выемка.
- `ZOOM`: логотип крупнее, только class cue.
- `REPEAT`: точное повторение.
- `STOP` / `ABSTAIN`: без нового наблюдения. Нельзя считать категорийную информацию достаточной для индивидуального `same/new`..

**Policy logic (not a prediction of results):**

Passive-fixed оставляет выбор ракурса расписанию; random не различает значимость категории и экземпляра; greedy-cue может предпочесть более заметный логотип; cost-blind identity-IG предпочитает ожидаемый сигнал о `same/new`; cost-aware учитывает цену относительно именно identity-сигнала; abstain-policy воздерживается, если не увидела различающую выемку, даже когда категория очевидна.

**Safe rule:** Не засчитывать category accuracy как within-class identity. `same` допустим после совпадения индивидуальной выемки; при её невидимости — `abstain`.

**Metric:** within-class balanced accuracy `same/new`, доля открытий ранее скрытого instance cue и отдельный учёт ошибок category-only.

**Risk/failure mode:** модель называет категорию правильно, но всё равно ошибочно выдаёт это за идентификацию экземпляра.

**Paired scene:** `06` · **Pair/control:** карточка 06 имеет тот же класс, общий логотип, исходную неопределённость и цену каждого вида, но никакая команда не показывает различающей индивидуальной метки. Пара отделяет полезность категории от сведения о конкретной сущности.

---

## AVO-03 · карточка 06 — категория видна, экземпляр неразличим

**Status:** SYNTHETIC / ILLUSTRATIVE / NOT TESTED · **Execution:** `NOT RUN`.

**Immutable IDs:** `E-AVO03-REF` → `E-AVO03-REPL`.

**Ground truth:** `new` · **Identifiability before:** `non_identifiable` · **After one action:** `non_identifiable`.

**Informative actions:** none · **Abstention allowed:** `true`.

**Holdout group:** none.

**Action-outcome summary (evaluator-only):**

`HOLD` — логотип и белая форма; `LEFT` — та же категорийная кромка; `RIGHT` — на обратной стороне видна та же треугольная выемка у обоих кандидатов, поэтому это только категорийное, не identity-свидетельство; `OBLIQUE/HEIGHT` — общий профиль диска; `ZOOM` — больший логотип; `REPEAT` — тот же кадр; `STOP/ABSTAIN` — новых сведений нет. Все изображения раскрывают максимум категорию/общие свойства или повтор; ни одно не разделяет `same` от `new`.

**Expected observations by action:**

- `HOLD`: логотип и белая форма.
- `LEFT`: та же категорийная кромка.
- `RIGHT`: на обратной стороне видна та же треугольная выемка у обоих кандидатов, поэтому это только категорийное, не identity-свидетельство.
- `OBLIQUE` / `HEIGHT`: общий профиль диска.
- `ZOOM`: больший логотип.
- `REPEAT`: тот же кадр.
- `STOP` / `ABSTAIN`: новых сведений нет. Все изображения раскрывают максимум категорию/общие свойства или повтор; ни одно не разделяет `same` от `new`..

**Policy logic (not a prediction of results):**

Passive-fixed видит предписанный кадр; random может увеличить категорийное сведение, но не identity; greedy-cue может выбрать самый заметный логотип и ошибочно принять его за цель, что в оценке не маркируется как identity-свидетельство; cost-blind/cost-aware не должны превращать отсутствие разделяющего сигнала в информативный; abstain-policy может корректно остановиться без ответа о скрытом ID.

**Safe rule:** `abstain` допустим и здесь предпочтительнее необоснованной уверенности; скрытое знание evaluator не является подсказкой.

**Metric:** within-class selective risk/coverage и доля ложного превращения class cue в identity cue, отдельно от точности категории.

**Risk/failure mode:** forced-choice на неидентифицируемой сцене, overclaim на общем логотипе или подсчёт неизвестного ответа как обычной ошибки same/new.

**Paired scene:** `05` · **Pair/control:** карточка 05 — same class, но после одного доступного действия появляется настоящий индивидуальный cue. Равны стартовые данные, время, цена, меню и бюджет; изменяется только идентифицируемость объекта на уровне экземпляра.

---

## AVO-04 · карточка 07 — одна разрешающая перепроверка

**Status:** SYNTHETIC / ILLUSTRATIVE / NOT TESTED · **Execution:** `NOT RUN`.

**Immutable IDs:** `E-AVO04-REF` → `E-AVO04-CONT`.

**Ground truth:** `same` · **Identifiability before:** `non_identifiable` · **After one action:** `identifiable`.

**Informative actions:** `OBLIQUE`, `HEIGHT` · **Abstention allowed:** `true`.

**Holdout group:** none.

**Action-outcome summary (evaluator-only):**

`HOLD` — головка винта, насечка закрыта; `LEFT`/`RIGHT` — боковой контур без нижней насечки; `OBLIQUE/HEIGHT` — нижний край и совпавшая насечка открыты, identity-информативно; `ZOOM` — больше тот же верхний вид, метка не читается; `REPEAT` — повтор исходного кадра; `STOP/ABSTAIN` — без дополнительного свидетельства. После informative вида ответить по насечке; после любого иного — identity остаётся неидентифицируемой, recheck исчерпан.

**Expected observations by action:**

- `HOLD`: головка винта, насечка закрыта.
- `LEFT` / `RIGHT`: боковой контур без нижней насечки.
- `OBLIQUE` / `HEIGHT`: нижний край и совпавшая насечка открыты, identity-информативно.
- `ZOOM`: больше тот же верхний вид, метка не читается.
- `REPEAT`: повтор исходного кадра.
- `STOP` / `ABSTAIN`: без дополнительного свидетельства. После informative вида ответить по насечке; после любого иного — identity остаётся неидентифицируемой, recheck исчерпан..

**Policy logic (not a prediction of results):**

Passive-fixed не может адаптивно проверить нижнюю грань; random может выбрать любой вид, не зная его пользы; greedy-cue может выбрать заметный крупный план, который не открывает насечку; cost-aware соотносит ожидаемую ценность одноразовой перепроверки с её ценой; abstain-policy может один раз проверить ожидаемо различающий вид, а затем воздержаться, если индивидуального сигнала нет.

**Safe rule:** Не повторять бесконечно; один доступный recheck, затем решение или abstain.

**Metric:** selective risk–coverage и калибровка/Brier с отдельной стратой informative recheck.

**Risk/failure mode:** не использовать разрешающий вид, преждевременно выбрать same/new либо продолжать неограниченные проверки.

**Paired scene:** `08` · **Pair/control:** карточка 08 имеет то же состояние камеры, видимый силуэт, расписание, меню и стоимость одного recheck, но в ней ни один разрешённый вид не создаёт уникального cue. Это парный контроль стратегии остановки, а не новый тест категории.

---

## AVO-04 · карточка 08 — истинная неидентифицируемость и допустимое abstain

**Status:** SYNTHETIC / ILLUSTRATIVE / NOT TESTED · **Execution:** `NOT RUN`.

**Immutable IDs:** `E-AVO04-REF` → `E-AVO04-REPL`.

**Ground truth:** `new` · **Identifiability before:** `non_identifiable` · **After one action:** `non_identifiable`.

**Informative actions:** none · **Abstention allowed:** `true`.

**Holdout group:** none.

**Action-outcome summary (evaluator-only):**

`HOLD` — тот же гладкий верх; `LEFT`/`RIGHT` — гладкие боковые поверхности без меток; `OBLIQUE/HEIGHT` — тот же профиль; `ZOOM` — более крупная гладкая поверхность; `REPEAT` — точные исходные пиксели; `STOP/ABSTAIN` — новых данных нет. Все доступные виды дают одинаковое свидетельство при `same` и `new`, то есть только категорию/повтор/неинформативное наблюдение. Действие не может сделать hidden ID видимым.

**Expected observations by action:**

- `HOLD`: тот же гладкий верх.
- `LEFT` / `RIGHT`: гладкие боковые поверхности без меток.
- `OBLIQUE` / `HEIGHT`: тот же профиль.
- `ZOOM`: более крупная гладкая поверхность.
- `REPEAT`: точные исходные пиксели.
- `STOP` / `ABSTAIN`: новых данных нет. Все доступные виды дают одинаковое свидетельство при `same` и `new`, то есть только категорию/повтор/неинформативное наблюдение. Действие не может сделать hidden ID видимым..

**Policy logic (not a prediction of results):**

Passive-fixed, random и greedy-cue могут выбирать разные виды, но ни один из них не должен получать кредит за identity-информацию, которой нет; cost-blind/cost-aware не находят основание для повторных бесполезных действий по карте наблюдений; abstain-policy завершает эпизод без forced choice либо после одного разрешённого бесполезного recheck.

**Safe rule:** Не угадывать ground truth и не трактовать доступный evaluator-only ID как модельное знание; остановиться и сообщить `abstain`.

**Metric:** selective risk–coverage, калибровка/Brier и стоимость бесполезного recheck на intrinsic non-identifiability страте.

**Risk/failure mode:** ложноуверенный `new` по самому факту окклюзии, бессмысленные повторные проверки или искусственное повышение coverage forced-choice ответами.

**Paired scene:** `07` · **Pair/control:** карточка 07 имеет тот же протокол одного recheck, но существует доступный индивидуальный вид. Сравнение относится к остановке и калибровке; скрытая метка карточки 08 не должна превращать его в угадайку.

---

## AVO-05 · карточка 09 — новый семейный контур объекта

**Status:** SYNTHETIC / ILLUSTRATIVE / NOT TESTED · **Execution:** `NOT RUN`.

**Immutable IDs:** `E-AVO05-REF` → `E-AVO05-CONT`.

**Ground truth:** `same` · **Identifiability before:** `non_identifiable` · **After one action:** `identifiable`.

**Informative actions:** `LEFT` · **Abstention allowed:** `true`.

**Holdout group:** новое семейство геометрии объекта.

**Action-outcome summary (evaluator-only):**

`HOLD` — фрагмент янтарного корпуса, индивидуальные отверстия закрыты; `LEFT` — оба отверстия и три зубца видны и совпадают с референсом, identity-информативно; `RIGHT` — гладкая боковая стенка, категория; `OBLIQUE/HEIGHT` — виден один зубец, но он общий; `ZOOM` — крупнее фрагмент без полного контура; `REPEAT` — тот же частичный вид; `STOP/ABSTAIN` — кадра нет. Никакой action не несёт label разбиения; только наблюдаемые отверстия могут разделять индивидуальность.

**Expected observations by action:**

- `HOLD`: фрагмент янтарного корпуса, индивидуальные отверстия закрыты.
- `LEFT`: оба отверстия и три зубца видны и совпадают с референсом, identity-информативно.
- `RIGHT`: гладкая боковая стенка, категория.
- `OBLIQUE` / `HEIGHT`: виден один зубец, но он общий.
- `ZOOM`: крупнее фрагмент без полного контура.
- `REPEAT`: тот же частичный вид.
- `STOP` / `ABSTAIN`: кадра нет. Никакой action не несёт label разбиения; только наблюдаемые отверстия могут разделять индивидуальность..

**Policy logic (not a prediction of results):**

Passive-fixed использует назначенный вид; random не знает принадлежность к удержанной группе; greedy-cue ориентируется на доступную форму, но не на split; cost-aware может выбрать `LEFT`, если ожидаемое identity-свидетельство оправдывает общую цену; abstain-policy может воздержаться, если cue после хода по-прежнему неполон. Никто не получает названия группы или provenance.

**Safe rule:** Не выводить `same` из того, что предмет «похож» или принадлежит знакомой категории; сравнивать только реально видимый экземплярный контур.

**Metric:** перенос на удержанной группе объектов и разброс/worst-group по заранее определённым факторам, отдельно false-same/false-new.

**Risk/failure mode:** решение по привычному шаблону категории, утечка семейства/seed/имени файла или вывод о переносе по одному примеру.

**Paired scene:** `10` · **Pair/control:** карточка 10 удерживает другой фактор — геометрию заслонки. В model-facing блоках обеих карточек намеренно отсутствуют слова «held-out», названия split, ID, seed, fold, provenance, ожидаемый правильный ход и evaluator-метки.

---

## AVO-05 · карточка 10 — новая геометрия заслонки

**Status:** SYNTHETIC / ILLUSTRATIVE / NOT TESTED · **Execution:** `NOT RUN`.

**Immutable IDs:** `E-AVO05-REF` → `E-AVO05-REPL`.

**Ground truth:** `new` · **Identifiability before:** `non_identifiable` · **After one action:** `identifiable`.

**Informative actions:** `OBLIQUE`, `HEIGHT` · **Abstention allowed:** `true`.

**Holdout group:** новое семейство геометрии заслонки.

**Action-outcome summary (evaluator-only):**

`HOLD` — верхняя часть белого жетона, нижний край закрыт; `LEFT`/`RIGHT` — боковые фрагменты за новой кромкой заслонки без насечки; `OBLIQUE/HEIGHT` — нижняя диагональная насечка открыта и не совпадает с референсом, identity-информативно; `ZOOM` — увеличен верхний участок, класс виден, насечка скрыта; `REPEAT` — прежние пиксели; `STOP/ABSTAIN` — новых данных нет. Различающий признак принадлежит объекту; сам факт необычной заслонки — не evidence о `same/new`.

**Expected observations by action:**

- `HOLD`: верхняя часть белого жетона, нижний край закрыт.
- `LEFT` / `RIGHT`: боковые фрагменты за новой кромкой заслонки без насечки.
- `OBLIQUE` / `HEIGHT`: нижняя диагональная насечка открыта и не совпадает с референсом, identity-информативно.
- `ZOOM`: увеличен верхний участок, класс виден, насечка скрыта.
- `REPEAT`: прежние пиксели.
- `STOP` / `ABSTAIN`: новых данных нет. Различающий признак принадлежит объекту; сам факт необычной заслонки — не evidence о `same/new`..

**Policy logic (not a prediction of results):**

Passive-fixed не адаптируется к скрытой кромке; random не имеет доступа к hidden split; greedy-cue учитывает наблюдаемую геометрию заслонки, но не её label; cost-aware сопоставляет ожидаемую identity-информацию `OBLIQUE/HEIGHT` с объявленной ценой; abstain-policy разрешает ответ лишь после видимого различия, иначе останавливается. Train/test provenance недоступен каждому методу.

**Safe rule:** Не считать новизну/форму заслонки сигналом о замене предмета; `new` допустим только после несовпадающей видимой насечки.

**Metric:** удержанный перенос по геометрии заслонки, разброс и worst-group анализ при равных бюджетах, с раздельными false-same/false-new.

**Risk/failure mode:** утечка названия удержанной группы, спутывание заслонки с объектом или вывод о переносе без представленных групп.

**Paired scene:** `09` · **Pair/control:** карточка 09 имеет тот же лимит одного хода/кадра и тот же вектор затрат; там удержан фактор формы самого объекта. В обоих случаях метаданные split, будущие кадры и oracle-label должны отсутствовать во входе модели.

---

## Integrity notes

In cards 06 and 08, ground truth is evaluator-known but remains non-identifiable before and after every allowed action; `abstain` is permitted. Category recognition is not instance identity.

For AVO-05 keep module/split labels, fold/train/validation/test, hidden IDs, seeds, filenames, ordering, provenance, future frames and oracle labels out of model payloads. Do not encode immutable IDs in filenames, seeds, watermarks, frame properties, ordering or public names.

Keep action-selected frames, passive-fixed frames and no-additional-frame controls distinct. Do not claim outcomes. Any future experiment requires a separately defined preregistration, criteria, cost weights and statistical plan; this package does not provide them or authorize a run.
