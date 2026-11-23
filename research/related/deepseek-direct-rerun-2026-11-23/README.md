# Прямой повтор DeepSeek V4 Pro и 4.1 Flash, 23 ноября 2026

**Статус:** RESEARCH, не Canon.
Отчёт: [`../deepseek-direct-rerun-2026-11-23.md`](../deepseek-direct-rerun-2026-11-23.md)

Свежий прогон только двух рук PR #62 (commit `8ad2ddb`) через официальный DeepSeek API `https://api.deepseek.com/chat/completions` и `DEEPSEEK_API_KEY`. OpenRouter не используется. Другие четыре модели не запускались.

Замороженный харнесс (сценарии, скорер, двухуровневый фильтр, soft L1) скопирован с PR #62. Температура не отправляется (thinking игнорирует её). `max_tokens=16384`, `reasoning_effort=high`. Свежий каталог результатов, существующие файлы не пропускаются.

```bash
python3 test_two_level_gate.py
python3 test_soft_l1.py
python3 runner.py --arm pro_high --fresh
python3 runner.py --arm flash_high --fresh
python3 score_soft.py
```
