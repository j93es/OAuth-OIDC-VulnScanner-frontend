import asyncio
import json
import os
import csv
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Agent, Browser, BrowserConfig, Controller
from browser_use.browser.context import BrowserContext, BrowserContextConfig
from lib.browser_config import browser_config_kwargs
from lib.is_html import is_html_url

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

1. Locate the Login Page
- Navigate to the **client (non-enterprise)** login page.
- If a **privacy policy / cookie / consent popup** appears, **dismiss** or **close** it before continuing.

2. On the Login Page
- Look for buttons like:
  - "Continue with Google"
  - "Sign in with GitHub"
  - "Login with Naver"
- ✅ Only proceed if **you clearly see a real SSO (social login) button**.
- ❌ Ignore or exclude:
  - Buttons with "Passkey"
  - Username/password fields
  - Email-based login
  - Login via certificate or mobile verification
  - Any non-OAuth login options

3. If at least one valid SSO login button is found:
- Try to **open it in a new tab**. If that’s not possible, **click it directly**.
- Capture the **first URL that the browser is redirected to** include query string. This URL should:
  ✅ Look like: `https://example.com/auth/google`
  ❌ Do NOT collect OAuth provider endpoint like: `https://accounts.google.com/...`
- Return the results in the following format:
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

4. If No SSO Login Buttons Are Found or an Error Occurs:
- ❌ Terminate the process immediately.
- Return an empty list: `[]`
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

# ── 인터랙티브 입력 루프 ──
async def loop():
    
    target_list = [
# "chefsdinners.com",
# "dungeonofdoomkemah.com",
# "fertittaentertainmentinc.com",
# "galvestonholidayinn.com",
# "goldennugget.com",
# "hunttinginn.com",
# "kemahbeerfest.com",
# "lilliesasiancuisine.com",
# "muer.com",
# "pleasurepier.com",
# "r-u-i.com",
# "sanluisresort.com",
"shoppostoak.com",
"thepostoak.com",
"thepostoakhotel.com",
"tilmanfertitta.com",
"wildwoodcasino.net",
"accounts.firefox.com",
"addons.allizom.org",
"api.profiler.firefox.com"]

    for url in target_list:
        await scan_one_url(f'https://{url}')

# ── 진입점 ──
if __name__ == "__main__":
    asyncio.run(loop())
