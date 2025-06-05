import asyncio
import json
import os
import csv
import argparse
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Agent, Browser, BrowserConfig, Controller
from browser_use.browser.context import BrowserContext, BrowserContextConfig
from lib.browser_config import browser_config_kwargs
from lib.is_html import is_html_url
from lib.read_txt import read_lines_between

load_dotenv()

if os.getenv("GOOGLE_API_KEY") is None:
    raise ValueError("GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")
if os.getenv("GOOGLE_MODEL") is None:
    raise ValueError("GOOGLE_MODEL 환경변수가 설정되지 않았습니다.")
if os.getenv("GOOGLE_PLANNER_MODEL") is None:
    raise ValueError("GOOGLE_PLANNER_MODEL 환경변수가 설정되지 않았습니다.")

# 출력 모델
class OAuth(BaseModel):
    provider: str
    oauth_uri: str

class OAuthList(BaseModel):
    oauth_providers: List[OAuth]

# Controller는 매번 새로 생성해도 무방합니다.
def make_controller():
    return Controller(output_model=OAuthList)

# Extended planner prompt
extend_planner_system_message = """
🎯 Mission: Collect Initial SSO Redirect URLs (For Browser Automation)

※ **절대로 구글 검색, Bing 검색 등 어떤 외부 검색 기능도 사용하지 말고, 주어진 로그인 페이지 URL을 직접 방문하여 탐색하세요.**

0. **초기 블록(Block) 체크**
   - 브라우저가 로그인 페이지에 접근하려 할 때, **페이지가 차단(blocked)** 되거나 **방화벽, CAPTCHA, 접근 제한** 등으로 인해 정상적으로 로드되지 않으면 즉시 프로세스를 종료하고 아래 JSON만 반환해야 합니다.  
     ```json
     [
       {
         "provider": "Blocked",
         "oauth_uri": "-"
       }
     ]
     ```
   - 이후 단계로 절대 넘어가지 않도록 합니다.

1. **로그인 페이지 탐색**
   - **클라이언트(비엔터프라이즈) 로그인 페이지**로 직접 이동합니다. (검색 엔진을 사용하여 찾아서는 안 됩니다.)
   - 접근 후 **개인정보/쿠키/동의 팝업**이 뜨면, 이를 반드시 **닫거나(Dismiss)** 처리하고 계속 진행합니다.
   - (이미 0단계에서 블록 여부를 확인했으므로, 이 단계에서는 페이지가 정상 로드되었다고 가정합니다.)

2. **SSO 버튼 식별**
   - 로그인 페이지에서 다음과 같은 소셜 로그인 버튼을 찾습니다:
     - “Continue with Google”
     - “Sign in with GitHub”
     - “Login with Naver”
   - ✅ **실제 SSO 버튼**임이 명확히 확인되는 경우에만 진행합니다.
   - ❌ 제외 대상:
     - “Passkey” 관련 버튼
     - 아이디/비밀번호 입력란
     - 이메일 기반 로그인
     - 인증서, 휴대폰 인증 등 비-OAuth 로그인 옵션

3. **리디렉션 URL 캡처**
   - 유효한 SSO 버튼을 하나 이상 찾았다면, 각각의 버튼을 **새 탭으로 열기**를 시도하거나, 불가능할 경우 **직접 클릭**합니다.
   - 클릭 후 첫 번째로 **리디렉션된 URL(쿼리 스트링 포함)**을 캡처합니다. 이 URL은:
     - ✅ 예시: `https://example.com/auth/google?include_all_params=...`
     - ❌ **OAuth 공급자 자체 엔드포인트** (예: `https://accounts.google.com/...`)는 수집하지 않습니다.
   - 만약 **반복 행동(looping)**이 감지될 경우(예: 동일한 버튼을 여러 번 열거나 페이지 간 반복 이동), 즉시 프로세스를 종료하고 **빈 배열**을 반환합니다:
     ```json
     []
     ```
   - 정상적으로 리디렉션 URL을 획득했다면, 아래 형식으로 결과를 수집합니다:
     ```json
     [
       {
         "provider": "Google",
         "oauth_uri": "https://example.com/auth/google?include_all_params=..."
       },
       {
         "provider": "GitHub",
         "oauth_uri": "https://example.com/auth/github?include_all_params=..."
       }
     ]
     ```

4. **SSO 버튼 미발견 또는 오류 발생 시**
   - 페이지 내부에 유효한 SSO 버튼이 전혀 없거나, 탐색 중 예기치 않은 오류가 발생하면 즉시 프로세스를 종료하고 **빈 배열**을 반환합니다:
     ```json
     []
     ```
"""

# ── URL별로 Browser를 새로 띄우는 함수 ──
async def scan_one_url(url: str):
    # 1) URL이 HTML 페이지인지 확인
    if not is_html_url(url):
        print(f"❌ {url} 은(는) HTML이 아닙니다. 스킵합니다.")
        return

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
    controller = make_controller()
    agent = Agent(
        browser_context=context,
        browser=browser,
        task=f"Go to {url}, navigate to the login page, and collect the OAuth provider buttons and their login URLs. Ignore Passkey.",
        llm=ChatGoogleGenerativeAI(model=os.getenv("GOOGLE_MODEL")),
        planner_llm=ChatGoogleGenerativeAI(model=os.getenv("GOOGLE_PLANNER_MODEL")),
        controller=controller,
        extend_planner_system_message=extend_planner_system_message,
    )
    
    try:

        # 4) 실제 스캔 실행
        response = await agent.run()
        final_result = response.final_result()
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

        # 7) Agent와 Browser 닫기
        await agent.close()           # Agent 내부 작업 정리
        await context.close()         # 브라우저 컨텍스트 종료 (탭/세션 닫기)
        await browser.close()         # 실제 브라우저 프로세스 종료
        
    except Exception as e:
        print(f"❌ Error scanning {url}: {e}")
        # 에러 발생 시에도 Agent와 Browser는 닫아야 합니다.
        await agent.close()
        await context.close()
        await browser.close()

async def loop(filepath: str, start_line: int, end_line: int):
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
        await scan_one_url(f'https://{url}')


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

    args = parser.parse_args()

    # 인자값을 비동기 함수에 전달
    asyncio.run(loop(
        filepath=args.file,
        start_line=args.start,
        end_line=args.end
    ))


if __name__ == "__main__":
    main()
