#!/bin/bash
set -u
ART="/workspace/Velantrim-Memory-Ruslan/research/related/deepseek-direct-rerun-2026-11-23"
LOGDIR="$ART/results/logs"
cd "$ART"
export TZ=Europe/Berlin
# Standing rule: never call OpenRouter in this rerun.
unset OPENROUTER_API_KEY || true
if [[ -z "${DEEPSEEK_API_KEY:-}" ]]; then
  echo "DEEPSEEK_API_KEY missing" >&2
  exit 2
fi
echo "==== supervisor start $(date '+%Y-%m-%d %H:%M:%S %Z') ===="
echo "cwd=$PWD url=https://api.deepseek.com/chat/completions arms=pro_high,flash_high fresh=1"

run_arm() {
  local arm="$1"
  echo "$(date '+%Y-%m-%d %H:%M:%S %Z') START $arm"
  python3 -u runner.py --arm "$arm" --fresh
  local ec=$?
  echo "$ec" > "$LOGDIR/${arm}.exit"
  echo "$(date '+%Y-%m-%d %H:%M:%S %Z') END $arm exit=$ec"
  return $ec
}

# Both DeepSeek arms in parallel. Each logs to its own file.
run_arm pro_high > "$LOGDIR/pro_high.log" 2>&1 &
pid_pro=$!
run_arm flash_high > "$LOGDIR/flash_high.log" 2>&1 &
pid_flash=$!
echo "pids pro_high=$pid_pro flash_high=$pid_flash"
wait "$pid_pro"
ec_pro=$?
wait "$pid_flash"
ec_flash=$?
echo "==== supervisor all arms finished $(date '+%Y-%m-%d %H:%M:%S %Z') ===="
echo "exits: pro_high=$(cat "$LOGDIR/pro_high.exit" 2>/dev/null || echo missing) flash_high=$(cat "$LOGDIR/flash_high.exit" 2>/dev/null || echo missing)"
if [[ $ec_pro -ne 0 || $ec_flash -ne 0 ]]; then
  exit 1
fi
exit 0
