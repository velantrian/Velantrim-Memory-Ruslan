#!/bin/bash
set -u
cd /workspace/Velantrim-Memory-Ruslan/research/related/six-model-two-level-2026-11-23
export PYTHONUNBUFFERED=1
LOGDIR=results/logs
mkdir -p "$LOGDIR"
exec >>"$LOGDIR/supervisor.log" 2>&1
echo "==== supervisor start $(date '+%Y-%m-%d %H:%M:%S Europe/Berlin') ===="

run_arm() {
  local arm="$1"
  echo "$(date '+%Y-%m-%d %H:%M:%S Europe/Berlin') START $arm pid=$$"
  python3 -u runner.py --arm "$arm"
  local ec=$?
  echo "$ec" > "$LOGDIR/${arm}.exit"
  echo "$(date '+%Y-%m-%d %H:%M:%S Europe/Berlin') END $arm exit=$ec"
  return $ec
}

# Wave 1: both DeepSeek arms + two OpenRouter arms (modest per provider)
run_arm pro_high &
echo $! > "$LOGDIR/pro_high.pid"
run_arm flash_high &
echo $! > "$LOGDIR/flash_high.pid"
run_arm sol &
echo $! > "$LOGDIR/sol.pid"
run_arm gemma4 &
echo $! > "$LOGDIR/gemma4.pid"

# Wave 2 OpenRouter: start after sol and gemma4 finish (DeepSeek keeps running)
wait "$(cat "$LOGDIR/sol.pid")" "$(cat "$LOGDIR/gemma4.pid")"
echo "$(date '+%Y-%m-%d %H:%M:%S Europe/Berlin') OpenRouter wave 1 done; starting wave 2"

run_arm nemotron35_super &
echo $! > "$LOGDIR/nemotron35_super.pid"
run_arm nemotron_ultra &
echo $! > "$LOGDIR/nemotron_ultra.pid"

wait
echo "==== supervisor all arms finished $(date '+%Y-%m-%d %H:%M:%S Europe/Berlin') ===="
echo "exits:" 
for a in pro_high flash_high sol gemma4 nemotron35_super nemotron_ultra; do
  if [[ -f $LOGDIR/${a}.exit ]]; then
    echo "  $a $(cat "$LOGDIR/${a}.exit")"
  else
    echo "  $a (no exit file)"
  fi
done
