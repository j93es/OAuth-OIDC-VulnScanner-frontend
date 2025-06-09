#!/bin/bash

# ── 설정 부분 ──
PYTHON_SCRIPT="main.py"
DOMAIN_FILE="./domains.txt"
CHUNK_SIZE=10
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

current=$START_LINE
while [ "$current" -le "$END_LINE" ]; do
  chunk_end=$(( current + CHUNK_SIZE - 1 ))
  if [ "$chunk_end" -gt "$END_LINE" ]; then
    chunk_end=$END_LINE
  fi

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Processing lines ${current} to ${chunk_end}..."
  uv run "$PYTHON_SCRIPT" -f "$DOMAIN_FILE" -s "$current" -e "$chunk_end" -skh $SKH_OPTION

  current=$(( chunk_end + 1 ))
  sleep 1  # 1초 대기
done

echo "모든 청크 처리 완료."
