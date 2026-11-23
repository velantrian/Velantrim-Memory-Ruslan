# DeepSeek V4 Pro high, max_tokens=32768, TASK-03 B-clean и C — 23 ноября 2026

**Статус:** RESEARCH, не Canon.
Отчёт: [`../deepseek-pro-32768-bclean-c-2026-11-23.md`](../deepseek-pro-32768-bclean-c-2026-11-23.md)

Серия, одобренная в аудите Codex: единственное отличие запроса от PR #63 (`main` @ `26d4016`) — `max_tokens=32768` вместо 16384. Модель `deepseek-v4-pro` через официальный API `https://api.deepseek.com/chat/completions` и `DEEPSEEK_API_KEY`; OpenRouter не используется. thinking включён, `reasoning_effort=high`, температура не отправляется.

Харнесс скопирован из `deepseek-direct-rerun-2026-11-23/` (PR #63) без изменений сценариев, скорера, двухуровневого фильтра и soft L1. Изменения:

- `client.py`: только рука `pro_high`, `max_tokens=32768`; клиентский тайм-аут сокета 1200 с (в API не отправляется).
- `runner.py`: TASK-03 только `B_clean` и `C` (11 + 11, пары идут подряд); в каждый файл пишется `messages_sha256`; флаг `--skip-canary` (канарейка не вызывалась, всего 22 вызова).
- Запуск через `results/logs/supervisor.sh` (nohup, `--allow-skip-existing`): при обрыве следующий проход дозапускает только недостающие или неуспешные прогоны. Понадобился один проход.

```bash
python3 test_two_level_gate.py
python3 test_soft_l1.py
python3 runner.py --arm pro_high --experiment task03 --skip-canary --allow-skip-existing
python3 score_soft.py
```

Soft L1 этой серии лежит в `results/pro_high/soft_summary.json`. `score_soft.py` попутно пересчитывает архивы PR #60/#61 в `results/retrospective/`; эта папка не коммитится, так как к серии не относится.
