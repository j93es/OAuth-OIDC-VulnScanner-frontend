import asyncio
import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from browser_use import Agent, BrowserSession, Controller
from patchright.async_api import async_playwright as async_patchright

from lib.browser_use.init_profile import GetProfile
from lib.browser_use.sensitive_data import GetSensitiveData
from lib.llm import CreateChatGoogle, get_prompt
from lib.utils import config, logger

# Exponential backoff settings
INITIAL_BACKOFF = int(os.getenv("INITIAL_BACKOFF", "60"))  # seconds
MAX_BACKOFF = int(os.getenv("MAX_BACKOFF", "600"))  # seconds


@dataclass
class RetryTask:
    """재시도할 작업을 나타내는 클래스"""

    task_type: str  # "oauth_list" or "oauth_login"
    url: str
    oauth_provider: Optional[str] = None
    retry_count: int = 0
    next_retry_time: Optional[datetime] = None
    max_retries: int = 5


# 전역 재시도 큐
retry_queue: list[RetryTask] = []
retry_queue_lock = asyncio.Lock()


async def add_to_retry_queue(task: RetryTask):
    """작업을 재시도 큐에 추가"""
    async with retry_queue_lock:
        # 중복 작업 확인
        existing_task = None
        for existing in retry_queue:
            if (
                existing.task_type == task.task_type
                and existing.url == task.url
                and existing.oauth_provider == task.oauth_provider
            ):
                existing_task = existing
                break

        if existing_task:
            # 기존 작업이 있으면 재시도 횟수 업데이트
            existing_task.retry_count = task.retry_count
            existing_task.next_retry_time = task.next_retry_time
            print(
                f"📝 기존 작업 업데이트: {task.task_type} - {task.url} (재시도: {task.retry_count})"
            )
        else:
            # 새 작업 추가
            retry_queue.append(task)
            print(
                f"➕ 재시도 큐에 작업 추가: {task.task_type} - {task.url} (재시도: {task.retry_count})"
            )


async def process_retry_queue():
    """재시도 큐 처리"""
    async with retry_queue_lock:
        now = datetime.now()
        ready_tasks = []

        for task in retry_queue[:]:  # 복사본에서 반복
            if task.next_retry_time and task.next_retry_time <= now:
                ready_tasks.append(task)
                retry_queue.remove(task)

        if ready_tasks:
            print(f"🔄 {len(ready_tasks)}개의 재시도 작업 처리 중...")

        for task in ready_tasks:
            try:
                if task.task_type == "oauth_list":
                    result = await _extract_oauth_list_internal(task.url)
                    if result:
                        print(f"✅ 재시도 성공: OAuth 리스트 추출 - {task.url}")
                    else:
                        await _handle_retry_failure(task)
                elif task.task_type == "oauth_login":
                    result = await _test_oauth_login_internal(
                        task.url, task.oauth_provider
                    )
                    if result:
                        print(
                            f"✅ 재시도 성공: {task.oauth_provider} 로그인 - {task.url}"
                        )
                    else:
                        await _handle_retry_failure(task)
            except Exception as e:
                print(f"❌ 재시도 중 에러: {e}")
                await _handle_retry_failure(task)


async def _handle_retry_failure(task: RetryTask):
    """재시도 실패 처리"""
    if task.retry_count < task.max_retries:
        task.retry_count += 1
        wait_time = min(INITIAL_BACKOFF * (2**task.retry_count), MAX_BACKOFF)
        task.next_retry_time = datetime.now() + timedelta(seconds=wait_time)
        await add_to_retry_queue(task)
        print(f"⏰ {wait_time}초 후 재시도 예정: {task.task_type} - {task.url}")
    else:
        print(f"❌ 최대 재시도 횟수 초과: {task.task_type} - {task.url}")
        logger(f"❌ 최대 재시도 횟수 초과: {task.task_type} - {task.url}")


async def get_retry_queue_status():
    """재시도 큐 상태 조회"""
    async with retry_queue_lock:
        return {
            "queue_length": len(retry_queue),
            "tasks": [
                {
                    "task_type": task.task_type,
                    "url": task.url,
                    "oauth_provider": task.oauth_provider,
                    "retry_count": task.retry_count,
                    "next_retry_time": (
                        task.next_retry_time.isoformat()
                        if task.next_retry_time
                        else None
                    ),
                }
                for task in retry_queue
            ],
        }


async def _run_agent_with_retry(agent_config):
    """Agent 실행을 위한 내부 헬퍼 함수 (재시도 로직 포함)"""
    agent = None
    session = None
    try_cnt = 0
    url = agent_config["url"]
    headless = os.getenv("HEADLESS", "False").lower() == "true"

    while try_cnt < 3:
        try:
            Profile = await GetProfile(headless=headless)
            session = BrowserSession(
                playwright=(await async_patchright().start()),
                browser_profile=Profile[0],
            )

            agent = Agent(browser_session=session, **agent_config["agent_params"])

            response = await agent.run()

            if any(
                keyword in str(response)
                for keyword in [
                    "429",
                    "resource_exhausted",
                    "resourceexhausted",
                    "quota",
                    "rate limit",
                    "too many requests",
                    "exceeded",
                    "limit reached",
                ]
            ):
                print(f"⚠️ API 쿼터 에러 발생, 재시도 큐에 추가: {url}")
                task = RetryTask(
                    task_type=agent_config.get("task_type", "unknown"),
                    url=url,
                    retry_count=try_cnt + 1,
                    next_retry_time=datetime.now() + timedelta(seconds=INITIAL_BACKOFF),
                )
                await add_to_retry_queue(task)
                return None
            
            # remove profile
            print(Profile)
            if Profile[1] and isinstance(Profile[1], str):
                print(1)
                shutil.rmtree(Profile[1], ignore_errors=True)
                print(f"🗑️ 임시 프로필 디렉토리 삭제 완료: {Profile[1]}")

            return response

        except Exception as e:
            # 일반 에러 처리
            try_cnt += 1
            if try_cnt >= 3:
                error_msg = f"최대 재시도 횟수 초과."
                logger(
                    f"❌ {url} - {agent_config['log_context']} 실패: {error_msg}: {e}"
                )
                print(f"❌ {url} - {agent_config['log_context']} 실패: {error_msg}")
                return None

            print(f"⚠️ 에러 발생: {e}. {try_cnt}번째 재시도 중...")
            await asyncio.sleep(30)
            continue
    return None


async def _extract_oauth_list_internal(url: str):
    """OAuth 리스트 추출 내부 함수 (재시도 큐에서 사용)"""
    target_url = url if url.startswith("http") else f"https://{url}"
    print(f"🔎 OAuth 리스트 추출 시작: {target_url}")
    prompt, model = get_prompt("auth")

    agent_config = {
        "url": target_url,
        "log_context": "OAuth 리스트 추출",
        "agent_params": {
            "initial_actions": [{"go_to_url": {"url": target_url, 'new_tab': False}}],
            "sensitive_data": GetSensitiveData(),
            "task": (
                "Navigate to the login page and identify all OAuth provider buttons (excluding Passkey). "
                "DO NOT click any OAuth buttons or attempt to login. "
                "Just find and list all available OAuth providers with their button texts or provider names. "
                "Return a list of OAuth providers found on the login page."
            ),
            "llm": CreateChatGoogle(config.GOOGLE_MODEL),
            "planner_llm": (
                CreateChatGoogle(config.GOOGLE_PLANNER_MODEL)
                if config.GOOGLE_PLANNER_MODEL
                and os.getenv("ENABLE_PLANNER_MODEL_OAUTH_LIST")
                else None
            ),
            "controller": Controller(
                output_model=model if not isinstance(model, str) else None,
                exclude_actions=["search_google", "unknown_action", "unkown"],
            ),
            "extend_system_message": prompt,
            "extend_planner_system_message": prompt,
        },
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


async def extract_oauth_list(url: str):
    """첫 번째 Agent: 로그인 페이지를 찾고 OAuth 리스트만 추출"""
    try:
        return await _extract_oauth_list_internal(url)
    except Exception as e:
        error_str = str(e).lower()
        if any(
            keyword in error_str
            for keyword in [
                "429",
                "resource_exhausted",
                "resourceexhausted",
                "quota",
                "rate limit",
                "too many requests",
                "exceeded",
                "limit reached",
            ]
        ):
            print(f"⚠️ API 쿼터 에러 발생, 재시도 큐에 추가: {url}")
            task = RetryTask(
                task_type="oauth_list",
                url=url,
                retry_count=1,
                next_retry_time=datetime.now() + timedelta(seconds=INITIAL_BACKOFF),
            )
            await add_to_retry_queue(task)
            return []
        else:
            raise e


async def _test_oauth_login_internal(url: str, oauth_provider: str):
    """OAuth 로그인 테스트 내부 함수 (재시도 큐에서 사용)"""
    target_url = url if url.startswith("http") else f"https://{url}"
    print(f"🔐 {oauth_provider} 로그인 시작: {target_url}")

    prompt, model = get_prompt(oauth_provider)

    agent_config = {
        "url": target_url,
        "log_context": f"{oauth_provider} 로그인",
        "agent_params": {
            "initial_actions": [{"go_to_url": {"url": target_url, 'new_tab': False}}],
            "sensitive_data": GetSensitiveData(),
            "task": (
                f"Navigate to the login page, find and click the {oauth_provider} OAuth button, "
                f"then follow the complete OAuth login flow as far as possible with a real user account. "
                f"Capture the final redirect URL after login completion. "
                f"If login fails or encounters errors, report the issue. "
                f"Focus only on {oauth_provider} - ignore other OAuth providers."
            ),
            "llm": CreateChatGoogle(config.GOOGLE_MODEL),
            "planner_llm": (
                CreateChatGoogle(config.GOOGLE_PLANNER_MODEL)
                if config.GOOGLE_PLANNER_MODEL
                and os.getenv("ENABLE_PLANNER_MODEL_OAUTH_LOGIN")
                else None
            ),
            "controller": Controller(
                output_model=model if not isinstance(model, str) else None,
                exclude_actions=["search_google", "unknown_action", "unkown"],
            ),
            "extend_system_message": prompt,
            "extend_planner_system_message": prompt,
        },
    }

    response = await _run_agent_with_retry(agent_config)

    if response and response.final_result():
        final_result = response.final_result()
        try:
            import json
            result_data = json.loads(final_result)
            status = result_data.get("status", "")
            
            if status == "success":
                print(f"✅ {oauth_provider} 로그인 완료")
                logger(f"✅ {url} - {oauth_provider} 로그인 결과: {final_result}")
                return True
            else:
                print(f"❌ {oauth_provider} 로그인 실패: {status}")
                logger(f"❌ {url} - {oauth_provider} 로그인 실패: {final_result}")
                return False
        except (json.JSONDecodeError, KeyError):
            print(f"❌ {oauth_provider} 결과 파싱 실패")
            return False

    print(f"❌ {oauth_provider} 로그인 실패")
    return False


async def test_oauth_login(url: str, oauth_provider: str):
    """두 번째 Agent: 특정 OAuth 제공자로 로그인 시도"""
    try:
        return await _test_oauth_login_internal(url, oauth_provider)
    except Exception as e:
        error_str = str(e).lower()
        if any(
            keyword in error_str
            for keyword in [
                "429",
                "resource_exhausted",
                "resourceexhausted",
                "quota",
                "rate limit",
                "too many requests",
                "exceeded",
                "limit reached",
            ]
        ):
            print(f"⚠️ API 쿼터 에러 발생, 재시도 큐에 추가: {oauth_provider} - {url}")
            task = RetryTask(
                task_type="oauth_login",
                url=url,
                oauth_provider=oauth_provider,
                retry_count=1,
                next_retry_time=datetime.now() + timedelta(seconds=INITIAL_BACKOFF),
            )
            await add_to_retry_queue(task)
            return False
        else:
            raise e


async def start_retry_queue_processor():
    """재시도 큐 처리기를 백그라운드에서 시작"""

    async def queue_processor():
        while True:
            try:
                await process_retry_queue()
                await asyncio.sleep(30)  # 30초마다 큐 확인
            except Exception as e:
                print(f"❌ 재시도 큐 처리 중 에러: {e}")
                await asyncio.sleep(60)  # 에러 발생 시 1분 대기

    # 백그라운드 태스크로 실행
    asyncio.create_task(queue_processor())
    print("🔄 재시도 큐 처리기 시작됨")


# 모듈 로딩 시 자동으로 백그라운드 처리기 시작
# (실제 애플리케이션에서는 main 함수에서 호출하는 것이 좋음)
def init_retry_system():
    """재시도 시스템 초기화"""
    print("🔧 재시도 시스템 초기화 중...")
    # 이 함수는 메인 애플리케이션에서 호출해야 함
