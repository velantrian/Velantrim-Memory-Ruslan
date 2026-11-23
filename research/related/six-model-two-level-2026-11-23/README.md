# Шестимодельный контрольный прогон ICT-01 и TASK-03, 23 ноября 2026

**Статус:** RESEARCH, не Canon.
Отчёт: [`../six-model-two-level-gate-2026-11-23.md`](../six-model-two-level-gate-2026-11-23.md)

Тот же протокол, что в PR #61, плюс офлайн-вариант SOFT L1 (не заменяет строгий фильтр).

Порядок рук: DeepSeek V4 Pro high, DeepSeek 4.1 Flash high, Nemotron 3.5 Super (`nvidia/nemotron-3.5-super-vl`), ChatGPT 6.2 Sol (`openai/gpt-6.2-sol`), Gemma 4 (`google/gemma-4-31b-it`), Nemotron 3 Ultra (свежий прогон `nvidia/nemotron-3-ultra-550b-a55b`).

```bash
python3 test_two_level_gate.py
python3 test_soft_l1.py
python3 runner.py --canary-only
python3 runner.py
python3 score_soft.py   # ретроспектива PR #60 и #61 + сводка новых рук
```
