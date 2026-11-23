# Контрольный прогон ICT-01 и TASK-03 на ChatGPT 6 Luna (high) и Nemotron 3 Ultra

**Статус:** RESEARCH, не Canon.
Отчёт: [`../control-model-two-level-gate-2026-11-23.md`](../control-model-two-level-gate-2026-11-23.md)

Сценарии, скорер и двухуровневый фильтр — замороженные копии с `main` после PR #60. Промпты не менялись.

| Рука | model | reasoning | max_tokens | температура |
|------|--------|-----------|------------|-------------|
| luna | `openai/gpt-6-luna` | `{"effort":"high"}` | 16384 (effort=high съедает ~80% лимита) | T=0×1 + T=0.7×10 |
| nemotron | `nvidia/nemotron-3-ultra-550b-a55b` (платный id, не `:free`) | не задаётся (канарейка всё равно вернула reasoning) | 16384 (канарейка показала reasoning по умолчанию) | та же схема |

Условия: ICT-01 A/B; TASK-03 A / B_clean / C; по 11. Фильтр двухуровневый по `report_draft`; `notes` — только `FLAG_REVIEW_NOTES`.

```bash
python3 test_two_level_gate.py
python3 runner.py --arm luna --canary-only
python3 runner.py --arm luna
python3 runner.py --arm nemotron
```
