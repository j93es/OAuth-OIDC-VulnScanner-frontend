from datetime import datetime
from pathlib import Path

# 미리 정해진 파일 경로
FILE_PATH = Path("data/log.txt")


def logger(msg: str) -> None:
    try:
        """
        msg 문자열을 파일 끝에 추가합니다.
        - 파일이 없으면 새로 생성
        - 디렉터리가 없으면 생성
        """
        # 상위 디렉터리 생성 (이미 있으면 무시)
        FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

        # 현재 시각 구해서 포맷팅
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

        # 메시지에 개행이 없으면 자동으로 붙이기
        newline = "" if msg.endswith("\n") else "\n"
        line = f"[{timestamp}] {msg}{newline}"

        # 'a' 모드: 파일이 없으면 생성, 있으면 이어쓰기
        with FILE_PATH.open(mode="a", encoding="utf-8") as f:
            f.write(line)
    except:
        print(msg)
