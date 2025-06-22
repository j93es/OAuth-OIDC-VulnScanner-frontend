import asyncio
import json
import os
import csv
import argparse
from pathlib import Path
import signal

from dotenv import load_dotenv

from browser_use import (
    Agent,
    BrowserSession,
    Controller,
    ActionResult,
)
from patchright.async_api import async_playwright as async_patchright, Page
from pydantic import BaseModel

from lib.utils import env_cheker
from lib.utils.backend_client import notify_backend
from lib.utils.browser_use import model
from lib.utils.browser_use.clean_resources import clean_resources
from lib.utils.browser_use.func import setup_storage_state
from lib.utils.browser_use.sensitive_data import GetSensitiveData
from lib.utils.config import BACKEND_URL, GOOGLE_MODEL, GOOGLE_PLANNER_MODEL
from lib.utils.is_html import is_html_url
from lib.utils.read_txt import read_lines_between
from lib.llm.prompt import extend_planner_system_message
from lib.utils.logger import logger
import lib.utils.browser_use as browser_use
from lib.llm import CreateChatGoogleGenerativeAI

load_dotenv(verbose=True, override=True)

# Exponential backoff settings
INITIAL_BACKOFF = int(os.getenv("INITIAL_BACKOFF", "60"))  # seconds
MAX_BACKOFF = int(os.getenv("MAX_BACKOFF", "600"))  # seconds

# 진행 상황 추적을 위한 전역 변수
current_progress = {"current_index": 0, "total": 0, "current_url": "", "start_line": 0}
progress_file = Path("data/scan_progress.json")

env_cheker()
if os.getenv("LMNR_PROJECT_API_KEY"):
    from lmnr import Laminar

    Laminar.initialize(project_api_key=os.getenv("LMNR_PROJECT_API_KEY"))


def save_progress():
    """현재 진행 상황을 파일에 저장"""
    with open(progress_file, "w", encoding="utf-8") as f:
        json.dump(current_progress, f, ensure_ascii=False, indent=2)


def load_progress():
    """이전 진행 상황을 파일에서 불러오기"""
    if os.path.exists(progress_file):
        try:
            with open(progress_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
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
    print(
        f"   - 진행률: {current_progress['current_index']}/{current_progress['total']} ({current_progress['current_index']/current_progress['total']*100:.1f}%)"
    )
    print("=" * 60)
    save_progress()
    print(f"💾 진행 상황이 {progress_file}에 저장되었습니다.")
    exit(0)


# 시그널 핸들러 등록
signal.signal(signal.SIGINT, signal_handler)


# ── URL별로 Browser를 새로 띄우는 함수 ──
async def scan_one_url(url: str, skip_html_check: bool = False):
    await setup_storage_state()
    target_url = url if url.startswith("http") else f"https://{url}"
    print(f"🚀 Starting scan for: {target_url}")

    # 1) URL이 HTML 페이지인지 확인
    if not is_html_url(target_url) and not skip_html_check:
        print(f"❌ {target_url} 은(는) HTML이 아닙니다. 스킵합니다.")
        return

    # Backend에 스캔 시작을 알림
    notify_backend(target_url)

    agent = None
    session = None
    try_cnt = 0
    while True:
        # BrowserSession에 profile 전달
        session = BrowserSession(
            playwright=(await async_patchright().start()),
            browser_profile=await browser_use.GetProfile(),
        )

        # Agent 생성 및 실행 (단일 try-except with 백오프)
        initial_actions = [{"open_tab": {"url": target_url}}]
        controller = Controller(
            output_model=model.BaseModel,
            exclude_actions=["search_google", "unknown_action", "unkown"],
        )

        print("🤖 LLM 모델 초기화 및 스캔 시작...")
        print("Available actions:", list(controller.registry.registry.actions.keys()))
        try:
            agent = Agent(
                browser_session=session,
                initial_actions=initial_actions,
                sensitive_data=GetSensitiveData(),
                task=(
                    "Navigate to the login page, identify all OAuth provider buttons (excluding Passkey), "
                    "and for each one: click the button, follow the full OAuth login flow as far as possible "
                    "with a real user account (without using a fake or non-existent account), and capture the "
                    "final redirect URL after login. Do not stop at just collecting the initial authorization URL—"
                    "actually perform the login step like a real user would. "
                    "If the OAuth buttons do not appear immediately, wait briefly to allow the page to load completely before proceeding. "
                    "Always log out before starting the login process, and make sure to attempt the login again from a clean state."
                ),
                llm=CreateChatGoogleGenerativeAI(GOOGLE_MODEL),
                planner_llm=(
                    CreateChatGoogleGenerativeAI(GOOGLE_PLANNER_MODEL)
                    if GOOGLE_PLANNER_MODEL
                    else None
                ),
                controller=controller,
                extend_planner_system_message=extend_planner_system_message,
            )
            response = await agent.run()
            final_result = response.final_result()

            if final_result is None:
                raise ValueError("final_result()가 None을 반환했습니다.")
        except Exception as e:
            await clean_resources(agent, session)
            # API 쿼터 문제인지 확인
            if "ResourceExhausted" in str(e) or "429" in str(e):
                wait = min(INITIAL_BACKOFF * (2**try_cnt), MAX_BACKOFF)
                print(f"⚠️ API 쿼터 에러: {e}. {wait}초 대기 후 재시도합니다...")
                await asyncio.sleep(wait)
                try_cnt += 1
                if try_cnt >= 3:
                    print(f"❌ {url} 스캔 실패: API 쿼터 문제가 지속됩니다.")
                    logger(f"❌ {url} 스캔 실패: API 쿼터 문제: {e}")
                    return
                continue
            # 일반 에러 처리
            try_cnt += 1
            if try_cnt >= 3:
                print(f"❌ {url} 스캔 실패: 에러: {e}")
                logger(f"❌ {url} 스캔 실패: 에러: {e}")
                return
            print(f"⚠️ 에러 발생: {e}. {try_cnt}번째 재시도 중...")
            await asyncio.sleep(30)
            continue

        # 스캔 결과 처리
        data = json.loads(final_result)
        try:
            oauth_entries = [model.OAuth(**entry) for entry in data["oauth_providers"]]
        except Exception as e:
            raise ValueError(f"결과 파싱 실패: {e}\n원본 결과: {final_result}")

        print("-" * 50)
        print(f"🔗 Scanned URL: {url}\n")
        print("🔐 Detected OAuth Providers and URLs:")
        for entry in oauth_entries:
            if "<" in entry.oauth_uri or "..." in entry.oauth_uri:
                print(
                    f"⚠️ WARNING: {entry.provider} URL may be masked or incomplete:\n{entry.oauth_uri}\n"
                )
            else:
                print(f"- {entry.provider}: {entry.oauth_uri}")
        print("-" * 50)

        # CSV에 저장 (append)
        csv_file = "./data/oauth_providers.csv"
        file_exists = os.path.isfile(csv_file)
        with open(csv_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["issuer", "provider", "oauth_uri"])
            for entry in oauth_entries:
                writer.writerow([url, entry.provider, entry.oauth_uri])
        await clean_resources(agent, session)
        break


async def loop(
    filepath: str, start_line: int, end_line: int, skip_html_check: bool = False
):
    # 인자값으로 받은 파일 경로와 줄 범위를 통해 도메인 리스트 생성
    target_list = read_lines_between(
        filepath=filepath, start_line=start_line, end_line=end_line
    )

    # 진행 상황 초기화
    current_progress["total"] = len(target_list)
    current_progress["start_line"] = start_line
    current_progress["current_index"] = 0

    # 이전 진행 상황 확인
    prev_progress = load_progress()
    if prev_progress and prev_progress.get("start_line") == start_line:
        print(f"📋 이전 진행 상황을 발견했습니다:")
        print(
            f"   - 이전 완료: {prev_progress['current_index']}/{prev_progress['total']}"
        )
        print(f"   - 마지막 처리: {prev_progress.get('current_url', 'N/A')}")

        resume = input("이어서 진행하시겠습니까? (y/n): ").lower().strip()
        if resume == "y":
            current_progress["current_index"] = prev_progress["current_index"]
            target_list = target_list[current_progress["current_index"] :]
            print(f"✅ {current_progress['current_index']}번째부터 재개합니다.")

    # (필요하다면) 강제 설정이 필요한 경우, 아래 주석을 해제하여 target_list[0] 등을 덮어쓸 수 있습니다.
    # target_list[0] = "velog.io"

    for i, url in enumerate(target_list):
        actual_index = current_progress["current_index"] + i
        current_progress["current_url"] = url
        current_progress["current_index"] = actual_index

        print(f"\n🔄 Processing {actual_index + 1}/{current_progress['total']}: {url}")
        print(f"📍 domains.txt의 {start_line + actual_index}번째 줄")

        # URL들 사이에 API 쿼터 회복을 위한 대기 시간 추가
        if actual_index > 0:
            print("⏳ API 쿼터 보호를 위해 30초 대기 중...")
            await asyncio.sleep(30)

        await scan_one_url(url, skip_html_check=skip_html_check)

        # 진행 상황 저장
        current_progress["current_index"] = actual_index + 1
        save_progress()

    print(f"\n🎉 모든 스캔이 완료되었습니다! ({current_progress['total']}개 URL)")
    # 완료 후 진행 상황 파일 삭제
    if os.path.exists(progress_file):
        os.remove(progress_file)


def main():
    parser = argparse.ArgumentParser(
        prog="domain_scanner",
        description="도메인 목록 파일에서 지정한 줄 범위를 읽어 SSO 스캔을 수행합니다.",
    )

    # 커맨드라인 인자로 받을 옵션들 정의
    parser.add_argument(
        "-f",
        "--file",
        type=str,
        required=True,
        help="도메인 목록이 들어 있는 텍스트 파일 경로 (예: ./domains.txt)",
    )
    parser.add_argument(
        "-s", "--start", type=int, required=True, help="읽기 시작 줄 번호 (1-based)"
    )
    parser.add_argument(
        "-e", "--end", type=int, required=True, help="읽기 종료 줄 번호 (1-based)"
    )
    parser.add_argument(
        "-skh",
        "--skip-html-check",
        type=bool,
        default=False,
        help="HTML 페이지 체크를 건너뛰고 모든 URL을 스캔합니다. (기본값: False)",
    )

    args = parser.parse_args()

    # 인자값을 비동기 함수에 전달
    asyncio.run(
        loop(
            filepath=args.file,
            start_line=args.start,
            end_line=args.end,
            skip_html_check=args.skip_html_check,
        )
    )


if __name__ == "__main__":
    main()
