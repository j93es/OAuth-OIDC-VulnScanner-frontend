import os

from dotenv import load_dotenv

from lib.utils.config import (
    BACKEND_URL,
    GOOGLE_API_KEY,
    GOOGLE_MODEL,
    GOOGLE_PLANNER_MODEL,
)

load_dotenv(override=True)


def show_info():
    print("🔧 환경 설정:")
    print(browser_use_version())
    print(f"🔗 Backend URL: {BACKEND_URL}")
    print(
        f"🔑 Google API Key: {'*' * (len(GOOGLE_API_KEY) - 4) + GOOGLE_API_KEY[-4:] if GOOGLE_API_KEY else None}"
    )
    print(f"🌐 Google Model: {GOOGLE_MODEL}")
    print(f"🌐 Google Planner Model: {GOOGLE_PLANNER_MODEL}")


def browser_use_version():
    try:
        # run uv pip show browser-use
        import subprocess

        result = subprocess.run(
            ["uv", "pip", "show", "browser-use"],
            capture_output=True,
            text=True,
            check=True,
        )

        print("📦 Browser Use 패키지 정보:")
        return result.stdout.strip()
    except ImportError:
        return None


def env_cheker():
    if GOOGLE_API_KEY is None:
        raise ValueError("GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")
    if GOOGLE_PLANNER_MODEL != None and (
        not os.getenv("ENABLE_PLANNER_MODEL_OAUTH_LOGIN")
        or not os.getenv("ENABLE_PLANNER_MODEL_OAUTH_LIST")
    ):
        print(
            "⚠️ GOOGLE_PLANNER_MODEL이 설정되어 있지만, ENABLE_PLANNER_MODEL_OAUTH_LOGIN 또는 ENABLE_PLANNER_MODEL_OAUTH_LIST가 활성화되지 않았습니다."
        )
        print(
            "⚠️ Planner 모델을 사용하려면 .env 파일에서 ENABLE_PLANNER_MODEL_OAUTH_LOGIN과 ENABLE_PLANNER_MODEL_OAUTH_LIST를 true로 설정하세요."
        )
        print(
            "‼️ 하지만 현재 Planner 모델을 사용하는 것이 권장되지 않습니다. 이 기능은 오작동을 일으킬 수 있습니다."
        )
        print("⚠️ 이 경고는 1초동안 정지합니다.")
        # 이 경고는 1초동안 sleep
        import time

        time.sleep(1)
