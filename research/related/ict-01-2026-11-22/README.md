# ICT-01 live run · 2026-11-22

Артефакты первого прогона Identity Continuity Test.

- Контракт: [`../ICT-01_harness.md`](../ICT-01_harness.md)
- Каркас на момент сверки: [`../ict01_harness.py`](../ict01_harness.py), коммит `33e15e0e915f66ead39c53ff7b2efa3987d65036`
- Отчёт: [`../ict-01-identity-continuity-run-2026-11-22.md`](../ict-01-identity-continuity-run-2026-11-22.md)

Статус: RESEARCH, не Canon.

## Содержимое

| Файл | Назначение |
|------|------------|
| `scenario.py` | Усложнённый fixture: соблазнительный источник X, тот же контракт A/B |
| `client.py` | Вызов DeepSeek; ключ читается только в момент запроса и не пишется на диск |
| `scoring.py` | Детерминированный скорер, правила зафиксированы до живого прогона |
| `test_scoring.py` | Офлайн-проверки скорера (без API) |
| `runner.py` | Протокол: канарейка + Condition A/B, N=10 при T=0.7 и 1 при T=0 |
| `results/` | Сырые ответы, таблица, сводка. Поля скоринга в `*_temp*.json` — pre-registered, их не переписывали |
| `results/openq_posthoc.json` | Поздняя поправка только по метрике открытого вопроса Q (ложное срабатывание regex); это не исходный счёт |

Запуск повторного прогона (создаст новые вызовы API):

```bash
python3 test_scoring.py
python3 runner.py --canary
python3 runner.py
```

Ключ: только переменная окружения `DEEPSEEK_API_KEY`. Не логировать и не коммитить.
