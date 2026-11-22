# Повтор ICT-01 и TASK-03 с корректными настройками DeepSeek

**Статус:** RESEARCH, не Canon.  
Отчёт: [`../deepseek-model-rerun-ict01-task03-2026-11-22.md`](../deepseek-model-rerun-ict01-task03-2026-11-22.md)

Сценарии, промпты, скорер и Gate скопированы из коммитов PR #57 (`a4c7cc8`) и PR #58 (`2327968`) в этот каталог. Сами PR #57 и #58 не изменялись. Ветки от `main` (`33e15e0`).

## Руки

| Рука | model | thinking | прочее |
|------|--------|----------|--------|
| R1 | `deepseek-flash` | disabled | T=0×1 + T=0.7×10, max_tokens=2000 |
| R2 | `deepseek-v4-pro` | disabled | та же схема температур, max_tokens=2000 |
| R3 | `deepseek-flash` | enabled, reasoning_effort=high | без temperature; max_tokens=16384 (thinking входит в лимит) |

Канарейки: `results/canaries/R{1,2,3}.json` — не перезаписываются.

```bash
python3 runner.py --canary-only
python3 runner.py
```
