import asyncio
import json
import os
import csv
import argparse
from pathlib import Path
import requests
import time
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.callbacks.base import BaseCallbackHandler
from browser_use import (
    Agent,
    BrowserSession,
    BrowserProfile,
    Controller,
)
from lib.is_html import is_html_url
from lib.read_txt import read_lines_between
from lib.prompt import extend_planner_system_message
from lib.logger import logger

load_dotenv()

if os.getenv("GOOGLE_API_KEY") is None:
    raise ValueError("GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")
if os.getenv("GOOGLE_MODEL") is None:
    raise ValueError("GOOGLE_MODEL 환경변수가 설정되지 않았습니다.")
if os.getenv("GOOGLE_PLANNER_MODEL") is None:
    raise ValueError("GOOGLE_PLANNER_MODEL 환경변수가 설정되지 않았습니다.")

backend_url = os.getenv("BACKEND_URL", "http://localhost:11081")


# API 쿼터 처리를 위한 콜백 핸들러
class QuotaExhaustedHandler(BaseCallbackHandler):
    def on_llm_error(self, error, **kwargs):
        if "ResourceExhausted" in str(error) or "429" in str(error):
            print("⚠️ API 쿼터가 소진되었습니다. 120초 대기 후 재시도합니다...")
            time.sleep(120)


def CreateChatGoogleGenerativeAI(model: str):
    """재시도 로직이 포함된 LLM 생성"""
    if model == "fallback":
        print("⚠️ Fallback 모델을 사용합니다. Envorinment 변수를 확인하세요.")
        print("⚠️ Model Gemini-2.0-flash-lite를 사용합니다.")
        model = "gemini-2.0-flash-lite"
    return ChatGoogleGenerativeAI(
        model=model,
        max_retries=10,  # 최대 재시도 횟수 증가
        model_kwargs={
            "request_timeout": 120,  # 타임아웃 시간 증가 (2분)
        },
        callbacks=[QuotaExhaustedHandler()],
        # API 호출 간격 조정
        temperature=0.1,
    )


# 출력 모델
class OAuth(BaseModel):
    provider: str
    oauth_uri: str


class OAuthList(BaseModel):
    oauth_providers: List[OAuth]


async def clean_resources(agent=None, session=None):
    """리소스를 정리하는 함수"""
    if agent:
        try:
            await agent.close()
        except Exception as e:
            print(f"⚠️ 에이전트 리소스 정리 실패: {e}")
    if session:
        try:
            await session.close()
        except Exception as e:
            print(f"⚠️ 세션 리소스 정리 실패: {e}")


# ── URL별로 Browser를 새로 띄우는 함수 ──
async def scan_one_url(url: str, skip_html_check: bool = False):
    target_url = url if url.startswith("http") else f"https://{url}"
    print(f"🚀 Starting scan for: {target_url}")

    # 1) URL이 HTML 페이지인지 확인
    if not is_html_url(target_url) and not skip_html_check:
        print(f"❌ {target_url} 은(는) HTML이 아닙니다. 스킵합니다.")
        return

    # Backend에 스캔 시작을 알림
    try:
        response = requests.post(
            f"{backend_url}/start", params={"url": target_url}, timeout=5
        )
        if response.status_code == 200:
            print(f"✅ Backend notified: {response.text}")
        else:
            print(f"⚠️ Backend notification failed: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(
            f"⚠️ Backend server not available at {backend_url}. Continuing without notification."
        )
    except requests.exceptions.Timeout:
        print(f"⚠️ Backend notification timed out. Continuing without notification.")
    except Exception as e:
        print(f"⚠️ Failed to notify backend: {e}")

    try_cnt = 0
    while True:
        proxy_host = os.getenv("PROXY_HOST")
        proxy_port = os.getenv("PROXY_PORT")
        proxy_url = None
        if proxy_host and proxy_port:
            proxy_url = f"http://{proxy_host}:{proxy_port}"
            print(f"🔗 Using proxy: {proxy_host}:{proxy_port}")
        else:
            print("🔗 No proxy configured, using direct connection.")

        # user_data_dir 설정
        user_data_path = Path("./data/user_data").resolve()
        user_data_path.mkdir(parents=True, exist_ok=True)

        # BrowserProfile에 모든 설정 포함
        profile = BrowserProfile(
            disable_security=True,
            stealth=True,
            headless=False,
            user_data_dir=str(user_data_path),
            viewport={"width": 1600, "height": 900},
            # 프록시 설정
            proxy={"server": proxy_url} if proxy_url else None,
            # 추가 args
            args=[
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--disable-site-isolation-trials",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-popup-blocking",
                "--disable-dev-shm-usage",
                f"--lang={os.getenv('LANG', 'en_US')}",
                "--ignore-certificate-errors",
                "--ignore-ssl-errors",
                "--allow-running-insecure-content",
            ],
        )

        # BrowserSession에 profile 전달
        session = BrowserSession(
            browser_profile=profile,
        )

        # Agent 생성
        initial_actions = [
            {"open_tab": {"url": target_url}},
        ]

        controller = Controller(output_model=OAuthList)

        # API 쿼터 문제 해결을 위한 LLM 생성
        print("🤖 LLM 모델 초기화 중...")

        try:
            agent = Agent(
                browser_session=session,
                initial_actions=initial_actions,
                task=f"Navigate to the login page, and collect the OAuth provider buttons and their login URLs. Ignore Passkey.",
                llm=CreateChatGoogleGenerativeAI(
                    os.getenv("GOOGLE_MODEL") or "fallback"
                ),
                planner_llm=CreateChatGoogleGenerativeAI(
                    os.getenv("GOOGLE_PLANNER_MODEL") or "fallback"
                ),
                controller=controller,
                extend_planner_system_message=extend_planner_system_message,
            )
        except Exception as e:
            print(f"⚠️ Agent 생성 실패: {e}")
            # API 쿼터 문제일 경우 더 긴 대기
            if "ResourceExhausted" in str(e) or "429" in str(e):
                print("⚠️ API 쿼터 문제로 인한 Agent 생성 실패. 5분 대기 후 재시도...")
                await asyncio.sleep(300)
            await clean_resources(agent=None, session=session)
            continue

        try:
            # 4) 실제 스캔 실행
            print("🔍 스캔 시작...")
            response = await agent.run()
            final_result = response.final_result()
            if final_result is None:
                raise ValueError("final_result()가 None을 반환했습니다.")

            data = json.loads(final_result)
            try:
                oauth_entries: List[OAuth] = [
                    OAuth(**entry) for entry in data["oauth_providers"]
                ]
            except Exception as e:
                raise ValueError(f"결과 파싱 실패: {e}\n원본 결과: {final_result}")

            # 5) 결과 출력
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

            # 6) CSV에 저장 (append)
            csv_file = "./oauth_providers.csv"
            file_exists = os.path.isfile(csv_file)
            with open(csv_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["issuer", "provider", "oauth_uri"])

                # 실제 데이터 저장
                for entry in oauth_entries:
                    writer.writerow([url, entry.provider, entry.oauth_uri])
            await clean_resources(agent, session)

            # 성공적으로 처리했으므로 반복문 탈출
            break

        except Exception as e:
            await clean_resources(agent, session)

            # API 쿼터 문제인지 확인
            if "ResourceExhausted" in str(e) or "429" in str(e):
                print(f"⚠️ API 쿼터 소진 에러: {e}")
                print("⚠️ 5분 대기 후 재시도합니다...")
                await asyncio.sleep(300)  # 5분 대기
                try_cnt += 1
                if try_cnt >= 3:
                    print(f"❌ {url} 스캔에 실패했습니다. API 쿼터 문제가 지속됩니다.")
                    logger(f"❌ {url} 스캔에 실패했습니다. API 쿼터 문제: {e}")
                    return
                continue

            if try_cnt >= 2:
                print(f"❌ {url} 스캔에 실패했습니다. 에러: {e}")
                logger(f"❌ {url} 스캔에 실패했습니다. 에러: {e}")
                return

            try_cnt += 1
            print(f"⚠️ 에러 발생: {e}. {try_cnt}번째 재시도 중...")

            # 일반 에러의 경우 짧게 대기
            await asyncio.sleep(30)
            # 반복문을 통해 재시도
            continue


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
