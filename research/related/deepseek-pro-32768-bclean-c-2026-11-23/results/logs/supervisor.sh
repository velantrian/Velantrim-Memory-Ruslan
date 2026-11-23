#!/bin/bash
# Resume-safe supervisor: each pass skips ok per-run files and re-runs only missing/failed ones.
cd "$(dirname "$0")/../.."
for pass in 1 2 3; do
  echo "[$(date '+%F %T %Z')] pass $pass" >> results/logs/supervisor.log
  python3 runner.py --arm pro_high --experiment task03 --skip-canary --allow-skip-existing >> results/logs/pro_high.log 2>&1
  rc=$?; echo "$rc" > results/logs/pro_high.exit
  echo "[$(date '+%F %T %Z')] pass $pass rc=$rc" >> results/logs/supervisor.log
  n=$(python3 -c "import json,glob;print(sum(1 for f in glob.glob('results/pro_high/task03/*_temp*.json') if json.load(open(f)).get('response',{}).get('ok')))")
  [ "$n" -ge 22 ] && break
done
echo DONE >> results/logs/supervisor.log
