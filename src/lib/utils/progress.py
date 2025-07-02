import json
import os
import signal
from pathlib import Path

# 진행 상황 추적을 위한 전역 변수
current_progress = {"current_index": 0, "total": 0, "current_url": "", "start_line": 0}
progress_file = Path("data/scan_progress.json")


def save_progress():
    """현재 진행 상황을 파일에 저장"""
    progress_file.parent.mkdir(parents=True, exist_ok=True)
    with open(progress_file, "w", encoding="utf-8") as f:
        json.dump(current_progress, f, ensure_ascii=False, indent=2)


def load_progress():
    """이전 진행 상황을 파일에서 불러오기"""
    if os.path.exists(progress_file):
        try:
            with open(progress_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    return None


def signal_handler(signum, frame):
    """Ctrl+C 시그널 핸들러"""
    print("\n" + "=" * 60)
    print("🛑 스캔이 중단되었습니다!")
    print(f"📊 진행 상황:")
    print(f"   - 전체: {current_progress['total']}개 URL")
    print(f"   - 완료: {current_progress['current_index']}개 URL")
    print(f"   - 현재 처리 중: {current_progress['current_url']}")
    print(
        f"   - domains.txt의 {current_progress['start_line'] + current_progress['current_index']}번째 줄"
    )
    if current_progress["total"] > 0:
        print(
            f"   - 진행률: {current_progress['current_index']}/{current_progress['total']} ({current_progress['current_index']/current_progress['total']*100:.1f}%)"
        )
    print("=" * 60)
    save_progress()
    print(f"💾 진행 상황이 {progress_file}에 저장되었습니다.")
    exit(0)


def setup_signal_handler():
    """시그널 핸들러 등록"""
    signal.signal(signal.SIGINT, signal_handler)
