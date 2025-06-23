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
from lib.llm.prompt import get_prompt
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


# ── OAuth 리스트 추출 Agent ──
async def extract_oauth_list(url: str, skip_html_check: bool = False):
    """첫 번째 Agent: 로그인 페이지를 찾고 OAuth 리스트만 추출"""
    await setup_storage_state()
    target_url = url if url.startswith("http") else f"https://{url}"
    print(f"� OAuth 리스트 추출 시작: {target_url}")

    # 1) URL이 HTML 페이지인지 확인
    if not is_html_url(target_url) and not skip_html_check:
        print(f"❌ {target_url} 은(는) HTML이 아닙니다. 스킵합니다.")
        return []

    agent = None
    session = None
    try_cnt = 0

    while True:
        session = BrowserSession(
            playwright=(await async_patchright().start()),
            browser_profile=await browser_use.GetProfile(),
        )

        initial_actions = [{"open_tab": {"url": target_url}}]
        controller = Controller(
            output_model=model.OAuthList,
            exclude_actions=["search_google", "unknown_action", "unkown"],
        )

        print("🤖 OAuth 리스트 추출 Agent 초기화...")

        try:
            agent = Agent(
                browser_session=session,
                initial_actions=initial_actions,
                sensitive_data=GetSensitiveData(),
                task=(
                    "Navigate to the login page and identify all OAuth provider buttons (excluding Passkey). "
                    "DO NOT click any OAuth buttons or attempt to login. "
                    "Just find and list all available OAuth providers with their button texts or provider names. "
                    "Return a list of OAuth providers found on the login page."
                ),
                llm=CreateChatGoogleGenerativeAI(GOOGLE_MODEL),
                planner_llm=(
                    CreateChatGoogleGenerativeAI(GOOGLE_PLANNER_MODEL)
                    if GOOGLE_PLANNER_MODEL
                    else None
                ),
                controller=controller,
                extend_planner_system_message=get_prompt("auth"),
            )

            response = await agent.run()
            final_result = response.final_result()

            if final_result is None:
                raise ValueError("OAuth 리스트 추출 결과가 None입니다.")

            data = json.loads(final_result)
            oauth_providers = data["oauth_providers"]  # 이제 문자열 배열
            oauth_entries = [model.OAuth(provider=provider) for provider in oauth_providers]

            await clean_resources(agent, session)
            return oauth_entries

        except Exception as e:
            await clean_resources(agent, session)
            # API 쿼터 문제인지 확인
            if "ResourceExhausted" in str(e) or "429" in str(e):
                wait = min(INITIAL_BACKOFF * (2**try_cnt), MAX_BACKOFF)
                print(f"⚠️ API 쿼터 에러: {e}. {wait}초 대기 후 재시도합니다...")
                await asyncio.sleep(wait)
                try_cnt += 1
                if try_cnt >= 3:
                    print(
                        f"❌ {url} OAuth 리스트 추출 실패: API 쿼터 문제가 지속됩니다."
                    )
                    logger(f"❌ {url} OAuth 리스트 추출 실패: API 쿼터 문제: {e}")
                    return []
                continue
            # 일반 에러 처리
            try_cnt += 1
            if try_cnt >= 3:
                print(f"❌ {url} OAuth 리스트 추출 실패: 에러: {e}")
                logger(f"❌ {url} OAuth 리스트 추출 실패: 에러: {e}")
                return []
            print(f"⚠️ 에러 발생: {e}. {try_cnt}번째 재시도 중...")
            await asyncio.sleep(30)
            continue


# ── 개별 OAuth 로그인 Agent ──
async def test_oauth_login(url: str, oauth_provider: str):
    """두 번째 Agent: 특정 OAuth 제공자로 로그인 시도"""
    await setup_storage_state()
    target_url = url if url.startswith("http") else f"https://{url}"
    print(f"🔐 {oauth_provider} 로그인 시작: {target_url}")

    agent = None
    session = None
    try_cnt = 0

    while True:
        session = BrowserSession(
            playwright=(await async_patchright().start()),
            browser_profile=await browser_use.GetProfile(),
        )

        initial_actions = [{"open_tab": {"url": target_url}}]
        controller = Controller(
            exclude_actions=["search_google", "unknown_action", "unkown"],
        )

        print(f"🤖 {oauth_provider} 로그인 Agent 초기화...")

        try:
            agent = Agent(
                browser_session=session,
                initial_actions=initial_actions,
                sensitive_data=GetSensitiveData(),
                task=(
                    f"Navigate to the login page, find and click the {oauth_provider} OAuth button, "
                    f"then follow the complete OAuth login flow as far as possible with a real user account. "
                    f"Capture the final redirect URL after login completion. "
                    f"If login fails or encounters errors, report the issue. "
                    f"Focus only on {oauth_provider} - ignore other OAuth providers."
                ),
                llm=CreateChatGoogleGenerativeAI(GOOGLE_MODEL),
                planner_llm=(
                    CreateChatGoogleGenerativeAI(GOOGLE_PLANNER_MODEL)
                    if GOOGLE_PLANNER_MODEL
                    else None
                ),
                controller=controller,
                extend_planner_system_message=get_prompt(oauth_provider),
            )

            response = await agent.run()
            final_result = response.final_result()

            print(f"✅ {oauth_provider} 로그인 완료")
            if final_result:
                logger(f"✅ {url} - {oauth_provider} 로그인 결과: {final_result}")

            await clean_resources(agent, session)
            return True

        except Exception as e:
            await clean_resources(agent, session)
            # API 쿼터 문제인지 확인
            if "ResourceExhausted" in str(e) or "429" in str(e):
                wait = min(INITIAL_BACKOFF * (2**try_cnt), MAX_BACKOFF)
                print(f"⚠️ API 쿼터 에러: {e}. {wait}초 대기 후 재시도합니다...")
                await asyncio.sleep(wait)
                try_cnt += 1
                if try_cnt >= 3:
                    print(
                        f"❌ {oauth_provider} 로그인 실패: API 쿼터 문제가 지속됩니다."
                    )
                    logger(
                        f"❌ {url} - {oauth_provider} 로그인 실패: API 쿼터 문제: {e}"
                    )
                    return False
                continue
            # 일반 에러 처리
            try_cnt += 1
            if try_cnt >= 3:
                print(f"❌ {oauth_provider} 로그인 실패: 에러: {e}")
                logger(f"❌ {url} - {oauth_provider} 로그인 실패: 에러: {e}")
                return False
            print(f"⚠️ 에러 발생: {e}. {try_cnt}번째 재시도 중...")
            await asyncio.sleep(30)
            continue


# ── 통합 스캔 함수 ──
async def scan_one_url(url: str, skip_html_check: bool = False):
    """URL 스캔 통합 함수: OAuth 리스트 추출 → 개별 OAuth 로그인 시도"""
    target_url = url if url.startswith("http") else f"https://{url}"
    print(f"🚀 스캔 시작: {target_url}")

    # Backend에 스캔 시작을 알림
    notify_backend(target_url)

    # 1단계: OAuth 리스트 추출
    oauth_entries = await extract_oauth_list(url, skip_html_check)

    if not oauth_entries:
        print(f"❌ {target_url}에서 OAuth 제공자를 찾을 수 없습니다.")
        return

    print("-" * 50)
    print(f"🔗 스캔 URL: {url}")
    print(f"🔐 발견된 OAuth 제공자들: {len(oauth_entries)}개")
    for entry in oauth_entries:
        print(f"  - {entry.provider}")
    print("-" * 50)

    # CSV에 OAuth 리스트 저장
    csv_file = "./data/oauth_providers.csv"
    file_exists = os.path.isfile(csv_file)
    with open(csv_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["issuer", "provider", "oauth_uri", "login_tested"])
        for entry in oauth_entries:
            writer.writerow([url, entry.provider, "", "pending"])  # oauth_uri는 빈 문자열

    # 2단계: 각 OAuth 제공자별로 개별 로그인 시도
    for i, oauth_entry in enumerate(oauth_entries):
        print(
            f"\n🔄 OAuth 로그인 테스트 {i+1}/{len(oauth_entries)}: {oauth_entry.provider}"
        )

        # OAuth 간 대기 시간
        if i > 0:
            print("⏳ OAuth 테스트 간 대기 중 (30초)...")
            await asyncio.sleep(30)

        # 개별 OAuth 로그인 시도
        success = await test_oauth_login(url, oauth_entry.provider)

        # 결과를 CSV에 업데이트 (간단하게 로그만 남김)
        status = "success" if success else "failed"
        print(f"📝 {oauth_entry.provider} 로그인 결과: {status}")


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
