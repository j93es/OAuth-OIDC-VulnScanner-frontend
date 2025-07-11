import json
import os, sys
import signal
import time
import threading
from pathlib import Path

# 진행 상황 추적을 위한 전역 변수
current_progress = {"current_index": 0, "total": 0, "current_url": "", "start_line": 0}
progress_file = Path("data/scan_progress.json")

# Ctrl+C 처리를 위한 전역 변수
ctrl_c_count = 0
last_ctrl_c_time = 0
shutdown_requested = False
shutdown_lock = threading.Lock()


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
    """Ctrl+C 시그널 핸들러 - 강제 종료"""
    global shutdown_requested
    
    with shutdown_lock:
        if shutdown_requested:
            # 이미 종료 요청이 있었다면 즉시 강제 종료
            print("\n� 강제 종료합니다!")
            os._exit(1)
        
        shutdown_requested = True
    
    print("\n" + "=" * 60)
    print("🛑 종료 신호를 받았습니다!")
    print(f"📊 현재 진행 상황:")
    print(f"   - 전체: {current_progress['total']}개 URL")
    print(f"   - 완료: {current_progress['current_index']}개 URL")
    print(f"   - 현재 처리 중: {current_progress['current_url']}")
    if current_progress.get('start_line'):
        print(f"   - domains.txt의 {current_progress['start_line'] + current_progress['current_index']}번째 줄")
    if current_progress["total"] > 0:
        print(f"   - 진행률: {current_progress['current_index']}/{current_progress['total']} ({current_progress['current_index']/current_progress['total']*100:.1f}%)")
    print("=" * 60)
    
    # 진행 상황 저장
    save_progress()
    print(f"💾 진행 상황이 {progress_file}에 저장되었습니다.")
    print("다음에 같은 명령어로 실행하면 이어서 진행할 수 있습니다.")
    print("\n🔄 정리 작업 중... (다시 Ctrl+C를 누르면 강제 종료)")
    
    # 정리 작업을 위해 잠시 대기 후 종료
    def delayed_exit():
        time.sleep(2)  # 2초 후 자동 종료
        print("\n✅ 정리 완료. 프로그램을 종료합니다.")
        os._exit(0)
    
    threading.Thread(target=delayed_exit, daemon=True).start()


def is_shutdown_requested():
    """종료 요청 상태를 확인하는 함수"""
    with shutdown_lock:
        return shutdown_requested

def setup_signal_handler():
    """시그널 핸들러 등록"""
    signal.signal(signal.SIGINT, signal_handler)
