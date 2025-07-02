import argparse
import os
import subprocess
import sys
from datetime import datetime

import requests

#!/usr/bin/env python3

# ── 설정 부분 ──
PYTHON_SCRIPT = "./src/main.py"
DOMAIN_FILE = "./data/domains.txt"
# ─────────────

def download_domains():
    """도메인 파일 다운로드"""
    try:
        print("도메인 파일 다운로드 중...")
        response = requests.get("https://f.imnya.ng/.whs/tp-domains/data/domains/latest.txt")
        response.raise_for_status()
        
        # 디렉토리가 없으면 생성
        os.makedirs(os.path.dirname("./data"), exist_ok=True)
        
        with open(DOMAIN_FILE, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("도메인 파일 다운로드 완료")
    except requests.RequestException as e:
        print(f"도메인 파일 다운로드 실패: {e}")
        sys.exit(1)

def run_script(start_line, end_line, skh_option):
    """Python 스크립트 실행"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{current_time}] Processing lines {start_line} to {end_line}...")

    try:
        command = [
            "uv", "run", PYTHON_SCRIPT,
            "-f", DOMAIN_FILE,
            "-s", str(start_line),
            "-e", str(end_line),
        ]
        if skh_option:
            command.append("--skip-html-check")

        subprocess.run(command, check=True)
    except subprocess.CalledProcessError:
        print("Python 스크립트 실행 실패")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="도메인 처리 스크립트 실행기",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  uv run run.py 10000 11000           # 10000~11000 라인 처리
  uv run run.py 10000 11000 --skh     # SKH 옵션 활성화
  uv run run.py 10000 11000 --no-download  # 다운로드 생략
        """
    )
    
    parser.add_argument("start_line", type=int, help="시작 라인 번호")
    parser.add_argument("end_line", type=int, help="종료 라인 번호")
    parser.add_argument("--skh", action="store_true", help="SKH 옵션 활성화")
    parser.add_argument("--no-download", action="store_true", help="도메인 파일 다운로드 생략")
    
    args = parser.parse_args()
    
    # 라인 범위 검증
    if args.start_line < 0 or args.end_line < 0:
        print("라인 번호는 0 이상이어야 합니다.")
        sys.exit(1)
    
    if args.start_line > args.end_line:
        print("시작 라인은 종료 라인보다 크거나 같아야 합니다.")
        sys.exit(1)
    
    # 도메인 파일 다운로드
    if not args.no_download:
        download_domains()
    elif not os.path.exists(DOMAIN_FILE):
        print(f"도메인 파일({DOMAIN_FILE})이 존재하지 않습니다. --no-download 옵션을 제거하거나 파일을 준비해주세요.")
        sys.exit(1)
    
    # 스크립트 실행
    run_script(args.start_line, args.end_line, args.skh)
    
    print("처리 완료.")

if __name__ == "__main__":
    main()