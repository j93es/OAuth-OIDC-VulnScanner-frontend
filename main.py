import asyncio
import json
import os
import csv
import argparse
import requests
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Agent, Browser, BrowserConfig, Controller
from browser_use.browser.context import BrowserContext, BrowserContextConfig
from lib.browser_config import browser_config_kwargs
from lib.is_html import is_html_url
from lib.read_txt import read_lines_between
from lib.prompt import extend_planner_system_message

load_dotenv()

if os.getenv("GOOGLE_API_KEY") is None:
    raise ValueError("GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")
if os.getenv("GOOGLE_MODEL") is None:
    raise ValueError("GOOGLE_MODEL 환경변수가 설정되지 않았습니다.")
if os.getenv("GOOGLE_PLANNER_MODEL") is None:
    raise ValueError("GOOGLE_PLANNER_MODEL 환경변수가 설정되지 않았습니다.")

backend_url = os.getenv("BACKEND_URL", "http://localhost:11081")

# 출력 모델
class OAuth(BaseModel):
    provider: str
    oauth_uri: str

class OAuthList(BaseModel):
    oauth_providers: List[OAuth]

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
        response = requests.post(f"{backend_url}/start", params={"url": target_url}, timeout=5)
        if response.status_code == 200:
            print(f"✅ Backend notified: {response.text}")
        else:
            print(f"⚠️ Backend notification failed: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"⚠️ Backend server not available at {backend_url}. Continuing without notification.")
    except requests.exceptions.Timeout:
        print(f"⚠️ Backend notification timed out. Continuing without notification.")
    except Exception as e:
        print(f"⚠️ Failed to notify backend: {e}")
        
    # 2) Browser + Context 생성
    browser = Browser(config=BrowserConfig(**browser_config_kwargs()))
    context = BrowserContext(
        browser=browser,
        config=BrowserContextConfig(
            wait_for_network_idle_page_load_time=3.0,
            window_width=1600,
            window_height=900,
            locale='en-US',
            highlight_elements=True,
            viewport_expansion=500,
            keep_alive=False
        )
    )

    # 3) Agent, Controller 생성
    initial_actions = [
        {'open_tab': {'url': target_url, 'wait_for_network_idle': True}},
    ]

    controller = Controller(output_model=OAuthList)
    agent = Agent(
        browser_context=context,
        browser=browser,
        initial_actions=initial_actions,
        task=f"Navigate to the login page, and collect the OAuth provider buttons and their login URLs. Ignore Passkey.",
        llm=ChatGoogleGenerativeAI(model=os.getenv("GOOGLE_MODEL")),
        planner_llm=ChatGoogleGenerativeAI(model=os.getenv("GOOGLE_PLANNER_MODEL")),
        controller=controller,
        extend_planner_system_message=extend_planner_system_message,
        retry_delay=60,
    )
    
    try_cnt = 0
    while True:
        try:
            # 4) 실제 스캔 실행
            response = await agent.run()
            final_result = response.final_reult()
            if final_result is None:
                raise ValueError("final_result()가 None을 반환했습니다.")

            data = json.loads(final_result)
            try:
                oauth_entries: List[OAuth] = [OAuth(**entry) for entry in data["oauth_providers"]]
            except Exception as e:
                raise ValueError(f"결과 파싱 실패: {e}\n원본 결과: {final_result}")

            # 5) 결과 출력
            print("-" * 50)
            print(f"🔗 Scanned URL: {url}\n")
            print("🔐 Detected OAuth Providers and URLs:")
            for entry in oauth_entries:
                if "<" in entry.oauth_uri or "..." in entry.oauth_uri:
                    print(f"⚠️ WARNING: {entry.provider} URL may be masked or incomplete:\n{entry.oauth_uri}\n")
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
                for entry in oauth_entries:
                    writer.writerow([url, entry.provider, entry.oauth_uri])
            print(f"✅ OAuth providers saved to {csv_file}\n")
            
            # 성공적으로 처리했으므로 반복문 탈출
            break
        
        except Exception as e:
            if try_cnt >= 3:
                print(f"❌ {url} 스캔에 실패했습니다. 에러: {e}")
                break
            try_cnt += 1
            print(f"⚠️ 에러 발생, 60초 대기 후 재시도합니다. (URL: {url})")

            # 1분 대기
            await asyncio.sleep(60)
            # 반복문을 통해 재시도
            continue
        
    # 리소스 정리
    try:
        await agent.close()
    except:
        pass
    try:
        await context.close()
    except:
        pass
    try:
        await browser.close()
    except:
        pass

async def loop(filepath: str, start_line: int, end_line: int, skip_html_check: bool = False):
    # 인자값으로 받은 파일 경로와 줄 범위를 통해 도메인 리스트 생성
    target_list = read_lines_between(
        filepath=filepath,
        start_line=start_line,
        end_line=end_line
    )

    # (필요하다면) 강제 설정이 필요한 경우, 아래 주석을 해제하여 target_list[0] 등을 덮어쓸 수 있습니다.
    # target_list[0] = "velog.io"

    for url in target_list:
        # scan_one_url은 외부에 정의된 비동기 함수라고 가정합니다.
        # 실제로 scan_one_url이 정의된 위치를 import하거나
        # 모듈 수준에 구현해두셔야 합니다.
        await scan_one_url(url, skip_html_check=skip_html_check)


def main():
    parser = argparse.ArgumentParser(
        prog="domain_scanner",
        description="도메인 목록 파일에서 지정한 줄 범위를 읽어 SSO 스캔을 수행합니다."
    )

    # 커맨드라인 인자로 받을 옵션들 정의
    parser.add_argument(
        "-f", "--file",
        type=str,
        required=True,
        help="도메인 목록이 들어 있는 텍스트 파일 경로 (예: ./domains.txt)"
    )
    parser.add_argument(
        "-s", "--start",
        type=int,
        required=True,
        help="읽기 시작 줄 번호 (1-based)"
    )
    parser.add_argument(
        "-e", "--end",
        type=int,
        required=True,
        help="읽기 종료 줄 번호 (1-based)"
    )
    parser.add_argument(
        "-skh", "--skip-html-check",
        type=bool,
        default=False,
        help="HTML 페이지 체크를 건너뛰고 모든 URL을 스캔합니다. (기본값: False)"
    )

    args = parser.parse_args()

    # 인자값을 비동기 함수에 전달
    asyncio.run(loop(
        filepath=args.file,
        start_line=args.start,
        end_line=args.end,
        skip_html_check=args.skip_html_check
    ))


if __name__ == "__main__":
    main()
