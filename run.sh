#!/bin/bash

# ── 설정 부분 ──
# 실행할 Python 스크립트 이름 (파일 확장자까지)
PYTHON_SCRIPT="main.py"

# 도메인 목록 파일 경로 (Python 스크립트 실행 시 -f 옵션에 전달)
DOMAIN_FILE="./domains.txt"

# 몇 줄씩(chunk) 나눠서 실행할지
CHUNK_SIZE=10
# ─────────────

# 인자 개수 확인
if [ $# -ne 2 ]; then
  echo "Usage: $0 <start_line> <end_line>"
  echo "예시) $0 10000 11000"
  exit 1
fi

START_LINE=$1
END_LINE=$2

# START_LINE부터 END_LINE까지 CHUNK_SIZE 만큼씩 반복
current=$START_LINE
while [ "$current" -le "$END_LINE" ]; do
  # 각 청크 구간의 마지막 줄 계산
  chunk_end=$(( current + CHUNK_SIZE - 1 ))
  if [ "$chunk_end" -gt "$END_LINE" ]; then
    chunk_end=$END_LINE
  fi

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Processing lines ${current} to ${chunk_end}..."
  # Python 스크립트 실행
  # -f DOMAIN_FILE: 도메인 목록 파일 경로
  # -s current  : 읽기 시작 줄
  # -e chunk_end: 읽기 끝 줄
  uv run "$PYTHON_SCRIPT" -f "$DOMAIN_FILE" -s "$current" -e "$chunk_end"

  # 다음 청크의 시작 값 설정
  current=$(( chunk_end + 1 ))
done

echo "모든 청크 처리 완료."
