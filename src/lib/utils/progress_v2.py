"""
종료 처리를 위한 개선된 모듈
browser-use의 pause 기능과 호환되도록 설계
"""
import json
import os
import signal
import time
import threading
import asyncio
from pathlib import Path

# 진행 상황 추적을 위한 전역 변수
current_progress = {"current_index": 0, "total": 0, "current_url": "", "start_line": 0}
progress_file = Path("data/scan_progress.json")

# 종료 관리를 위한 전역 변수
shutdown_requested = False
shutdown_lock = threading.Lock()
original_handler = None


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


def request_shutdown():
    """종료 요청 함수 - 외부에서 호출 가능"""
    global shutdown_requested
    with shutdown_lock:
        if not shutdown_requested:
            shutdown_requested = True
            print("\n🛑 종료가 요청되었습니다. 현재 작업을 완료한 후 종료합니다...")
            save_progress()
            print(f"💾 진행 상황이 {progress_file}에 저장되었습니다.")


def is_shutdown_requested():
    """종료 요청 상태를 확인하는 함수"""
    with shutdown_lock:
        return shutdown_requested


def cleanup_signal_handler():
    """signal handler를 정리하고 원래 상태로 복원"""
    global original_handler
    if original_handler is not None:
        signal.signal(signal.SIGINT, original_handler)
        original_handler = None


def setup_minimal_signal_handler():
    """최소한의 signal handler만 설정 - browser-use와 충돌 방지"""
    global original_handler
    
    # 원래 핸들러 저장
    original_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    def graceful_signal_handler(signum, frame):
        """우아한 종료를 위한 최소한의 signal handler"""
        print("\n🛑 종료 신호를 받았습니다...")
        save_progress()
        print(f"💾 진행 상황이 {progress_file}에 저장되었습니다.")
        
        # 원래 핸들러로 복원하고 신호를 다시 발생시킴
        signal.signal(signal.SIGINT, original_handler)
        os.kill(os.getpid(), signal.SIGINT)
    
    signal.signal(signal.SIGINT, graceful_signal_handler)


class GracefulShutdown:
    """컨텍스트 매니저로 사용할 수 있는 우아한 종료 클래스"""
    
    def __init__(self):
        self.original_handler = None
        
    def __enter__(self):
        self.original_handler = signal.signal(signal.SIGINT, self._signal_handler)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.original_handler is not None:
            signal.signal(signal.SIGINT, self.original_handler)
            
    def _signal_handler(self, signum, frame):
        """내부 signal handler"""
        request_shutdown()
        # 원래 핸들러 복원 후 신호 재전송
        signal.signal(signal.SIGINT, self.original_handler)
        os.kill(os.getpid(), signal.SIGINT)


# 기존 함수들과의 호환성을 위한 별칭
def setup_signal_handler():
    """기존 코드와의 호환성을 위한 함수"""
    pass  # browser-use의 signal handler를 방해하지 않음


def signal_handler(signum, frame):
    """기존 코드와의 호환성을 위한 함수"""
    request_shutdown()
