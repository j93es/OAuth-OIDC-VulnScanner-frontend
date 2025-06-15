import asyncio
import json
import os
import csv
import argparse

from dotenv import load_dotenv

from browser_use import (
    Agent,
    BrowserSession,
    Controller,
)
from patchright.async_api import async_playwright as async_patchright

from lib.utils import env_cheker
from lib.utils.backend_client import notify_backend
from lib.utils.browser_use import model
from lib.utils.browser_use.clean_resources import clean_resources
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

env_cheker()
if os.getenv("LMNR_PROJECT_API_KEY"):
    from lmnr import Laminar

    Laminar.initialize(project_api_key=os.getenv("LMNR_PROJECT_API_KEY"))


# ── URL별로 Browser를 새로 띄우는 함수 ──
async def scan_one_url(url: str, skip_html_check: bool = False):
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
            browser_profile=browser_use.profile,
        )

        # Agent 생성 및 실행 (단일 try-except with 백오프)
        initial_actions = [{"open_tab": {"url": target_url}}]
        controller = Controller(output_model=model.BaseModel)
        print("🤖 LLM 모델 초기화 및 스캔 시작...")
        try:
            agent = Agent(
                browser_session=session,
                initial_actions=initial_actions,
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
                planner_llm=CreateChatGoogleGenerativeAI(GOOGLE_PLANNER_MODEL),
                controller=controller,
                extend_planner_system_message=extend_planner_system_message(),
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
        csv_file = "./oauth_providers.csv"
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

    # (필요하다면) 강제 설정이 필요한 경우, 아래 주석을 해제하여 target_list[0] 등을 덮어쓸 수 있습니다.
    # target_list[0] = "velog.io"

    for i, url in enumerate(target_list):
        print(f"\n🔄 Processing {i+1}/{len(target_list)}: {url}")

        # URL들 사이에 API 쿼터 회복을 위한 대기 시간 추가
        if i > 0:
            print("⏳ API 쿼터 보호를 위해 30초 대기 중...")
            await asyncio.sleep(30)

        await scan_one_url(url, skip_html_check=skip_html_check)


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
