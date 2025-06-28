import asyncio
import os
import json

from browser_use import Agent, BrowserSession, Controller
from patchright.async_api import async_playwright as async_patchright

from lib.browser_use import (
    GetProfile,
    GetSensitiveData,
    clean_resources,
)
from lib.utils import (
    logger,
    config,
)
from lib.llm import CreateChatGoogleGenerativeAI, get_prompt

# Exponential backoff settings
INITIAL_BACKOFF = int(os.getenv("INITIAL_BACKOFF", "60"))  # seconds
MAX_BACKOFF = int(os.getenv("MAX_BACKOFF", "600"))  # seconds

async def _run_agent_with_retry(agent_config):
    """Agent 실행을 위한 내부 헬퍼 함수 (재시도 로직 포함)"""
    agent = None
    session = None
    try_cnt = 0
    url = agent_config["url"]
    
    while try_cnt < 3:
        try:
            session = BrowserSession(
                playwright=(await async_patchright().start()),
                browser_profile=await GetProfile(),
            )

            agent = Agent(
                browser_session=session,
                **agent_config["agent_params"]
            )

            response = await agent.run()
            await clean_resources(agent, session)
            return response

        except Exception as e:
            await clean_resources(agent, session)
            
            if "ResourceExhausted" in str(e) or "429" in str(e):
                wait = min(INITIAL_BACKOFF * (2**try_cnt), MAX_BACKOFF)
                print(f"⚠️ API 쿼터 에러: {e}. {wait}초 대기 후 재시도합니다...")
                await asyncio.sleep(wait)
                try_cnt += 1
                if try_cnt >= 3:
                    error_msg = f"API 쿼터 문제가 지속됩니다."
                    logger(f"❌ {url} - {agent_config['log_context']} 실패: {error_msg}: {e}")
                    print(f"❌ {url} - {agent_config['log_context']} 실패: {error_msg}")
                    return None
                continue
            
            # 일반 에러 처리
            try_cnt += 1
            if try_cnt >= 3:
                error_msg = f"최대 재시도 횟수 초과."
                logger(f"❌ {url} - {agent_config['log_context']} 실패: {error_msg}: {e}")
                print(f"❌ {url} - {agent_config['log_context']} 실패: {error_msg}")
                return None
            
            print(f"⚠️ 에러 발생: {e}. {try_cnt}번째 재시도 중...")
            await asyncio.sleep(30)
            continue
    return None


async def extract_oauth_list(url: str):
    """첫 번째 Agent: 로그인 페이지를 찾고 OAuth 리스트만 추출"""
    target_url = url if url.startswith("http") else f"https://{url}"
    print(f"🔎 OAuth 리스트 추출 시작: {target_url}")
    prompt, model = get_prompt("auth")

    agent_config = {
        "url": target_url,
        "log_context": "OAuth 리스트 추출",
        "agent_params": {
            "initial_actions": [{"open_tab": {"url": target_url}}],
            "sensitive_data": GetSensitiveData(),
            "task": (
                "Navigate to the login page and identify all OAuth provider buttons (excluding Passkey). "
                "DO NOT click any OAuth buttons or attempt to login. "
                "Just find and list all available OAuth providers with their button texts or provider names. "
                "Return a list of OAuth providers found on the login page."
            ),
            "llm": CreateChatGoogleGenerativeAI(config.GOOGLE_MODEL),
            "planner_llm": (
                CreateChatGoogleGenerativeAI(config.GOOGLE_PLANNER_MODEL)
                if config.GOOGLE_PLANNER_MODEL
                else None
            ),
            "controller": Controller(
                output_model=model if not isinstance(model, str) else None,
                exclude_actions=["search_google", "unknown_action", "unkown"],
            ),
            "extend_planner_system_message": prompt,
        }
    }

    response = await _run_agent_with_retry(agent_config)

    if not response:
        return []

    final_result = response.final_result()
    if not final_result:
        print("OAuth 리스트 추출 결과가 없습니다.")
        return []

    try:
        data = json.loads(final_result)
        print(final_result)
        oauth_providers = data.get("sso_list", [])
        if not oauth_providers:
            print("❌ OAuth 제공자가 없습니다.")
            logger(f"❌ {url} - OAuth 제공자 없음: {final_result}")
            return []
        print(f"✅ OAuth 제공자 추출 완료: {oauth_providers}")
        return oauth_providers
    except (json.JSONDecodeError, KeyError) as e:
        print(f"❌ 결과 파싱 실패: {e}")
        logger(f"❌ {url} 결과 파싱 실패: {final_result}")
        return []


async def test_oauth_login(url: str, oauth_provider: str):
    """두 번째 Agent: 특정 OAuth 제공자로 로그인 시도"""
    target_url = url if url.startswith("http") else f"https://{url}"
    print(f"🔐 {oauth_provider} 로그인 시작: {target_url}")

    prompt, model = get_prompt(oauth_provider)

    agent_config = {
        "url": target_url,
        "log_context": f"{oauth_provider} 로그인",
        "agent_params": {
            "initial_actions": [{"open_tab": {"url": target_url}}],
            "sensitive_data": GetSensitiveData(),
            "task": (
                f"Navigate to the login page, find and click the {oauth_provider} OAuth button, "
                f"then follow the complete OAuth login flow as far as possible with a real user account. "
                f"Capture the final redirect URL after login completion. "
                f"If login fails or encounters errors, report the issue. "
                f"Focus only on {oauth_provider} - ignore other OAuth providers."
            ),
            "llm": CreateChatGoogleGenerativeAI(config.GOOGLE_MODEL),
            "planner_llm": (
                CreateChatGoogleGenerativeAI(config.GOOGLE_PLANNER_MODEL)
                if config.GOOGLE_PLANNER_MODEL and os.getenv("ENABLE_PLANNER_MODEL_OAUTH_LOGIN")
                else None
            ),
            "controller": Controller(
                output_model=model if not isinstance(model, str) else None,
                exclude_actions=["search_google", "unknown_action", "unkown"],
            ),
            "extend_planner_system_message": prompt,
        }
    }

    response = await _run_agent_with_retry(agent_config)

    if response and response.final_result():
        final_result = response.final_result()
        print(f"✅ {oauth_provider} 로그인 완료")
        logger(f"✅ {url} - {oauth_provider} 로그인 결과: {final_result}")
        return True
    
    print(f"❌ {oauth_provider} 로그인 실패")
    return False