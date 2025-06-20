#!/bin/bash

# ── 설정 부분 ──
PYTHON_SCRIPT="main.py"
DOMAIN_FILE="./data/domains.txt"
# ─────────────

curl "https://f.imnya.ng/.whs/tp-domains/data/domains/latest.txt" -o $DOMAIN_FILE

# 인자 개수 확인
if [ $# -lt 2 ]; then
  echo "Usage: $0 <start_line> <end_line> [skh_option]"
  echo "예시) $0 10000 11000 True"
  exit 1
fi

START_LINE=$1
END_LINE=$2
SKH_OPTION=$3

if [ -z "$SKH_OPTION" ]; then
  SKH_OPTION="False"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Processing lines ${START_LINE} to ${END_LINE}..."
uv run "$PYTHON_SCRIPT" -f "$DOMAIN_FILE" -s "$START_LINE" -e "$END_LINE" -skh $SKH_OPTION

echo "처리 완료."
