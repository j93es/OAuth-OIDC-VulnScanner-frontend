from lib.utils.config import (
    BACKEND_URL,
    GOOGLE_API_KEY,
    GOOGLE_MODEL,
    GOOGLE_PLANNER_MODEL,
)


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
