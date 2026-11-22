# TASK-03 · Gate как код · прогон 2026-11-22

- Контракт ICT-01: [`../ICT-01_harness.md`](../ICT-01_harness.md) (на `main`, `33e15e0`)
- Модуль фильтра: [`../ict01_gate.py`](../ict01_gate.py)
- Юнит-тесты фильтра: [`../test_ict01_gate.py`](../test_ict01_gate.py)
- Отчёт: [`../task-03-gate-as-code-2026-11-22.md`](../task-03-gate-as-code-2026-11-22.md)

Статус: RESEARCH, не Canon. Ветка от `main`, без файлов ICT-01 PR #57: сценарий и скорер скопированы и отмечены.

## Содержимое

| Файл | Назначение |
|------|------------|
| `scenario.py` | Три формы ограничения (текст / структурированный GATE / нет в промпте) + усиленный запрос заказчика |
| `scoring.py` | Скорер, зафиксированный до прогона; правило Q — поправка ICT-01, уже pre-registered |
| `test_scoring.py` | Офлайн-проверки скорера, включая ложный regex ICT-01 |
| `client.py` / `runner.py` | DeepSeek; ключ только в момент вызова |
| `results/` | Сырые ответы и таблица. Поля скоринга не переписывались после прогона |

```bash
python3 ../test_ict01_gate.py
python3 test_scoring.py
python3 runner.py --canary
python3 runner.py
```
