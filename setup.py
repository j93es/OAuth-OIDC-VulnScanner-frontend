import os
import subprocess
import webbrowser
import asyncio
from browser_use import BrowserProfile, Agent
from browser_use.llm import ChatGoogle
from dotenv import load_dotenv
import threading
load_dotenv(verbose=True, override=True)

os.makedirs(os.path.dirname("./data"), exist_ok=True)

def create_file_from_example(target: str, example: str) -> bool:
    if not os.path.exists(target):
        if os.path.exists(example):
            with open(example, 'r', encoding='utf-8') as example_file, \
                    open(target, 'w', encoding='utf-8') as target_file:
                target_file.write(example_file.read())
                #os.startfile(target)
            print(f"✅ {target} 파일이 {example}에서 생성되었습니다.")
            return True
        else:
            print(f"⚠️ {example} 파일이 존재하지 않습니다. {target} 생성에 실패했습니다.")
    else:
        print(f"ℹ️ {target} 파일이 이미 존재합니다.")
    return False


def install_playwright_chrome():
    print("\n🛠️ Playwright의 Chrome을 설치 중입니다...")
    try:
        subprocess.run(['uv', 'run', 'playwright', 'install', 'chrome'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("✅ Playwright Chrome 설치 완료.")
    except subprocess.CalledProcessError as e:
        if "already" in e.stdout.decode():
            print("ℹ️ Chrome이 이미 설치되어 있습니다.")
        else:
            print(f"❌ Playwright 설치 실패: {e}")
    print("\n")


def prompt_yes_no(message: str) -> bool:
    print(message, end="")
    return input().strip().lower() in ['y', 'yes']

def i_dont_like_windows():
    # Windows인지 확인
    if os.name != 'nt':
        return
    else:
        # run (Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Nls\CodePage").ACP
        try:
            result = subprocess.run(
                ['powershell', '-Command', '(Get-ItemProperty "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Nls\\CodePage").ACP'],
                capture_output=True,
                text=True,
                check=True
            )
            acp = result.stdout.strip()
            if acp == '65001':
                print("현재 Active Code Page가 UTF-8로 설정되어 있습니다.")
                return
            else:
                print("현재 Active Code Page가 UTF-8로 설정되어 있지 않습니다.")
        except subprocess.CalledProcessError as e:
            print(f"코드 페이지 확인 실패: {e}")
        print("=======================================================")
        print("\n⚠️ Windows에서는 인코딩 문제가 발생합니다.")
        print("👉 엔터를 누르면 자동으로 intl.cpl이 열립니다.")
        print("👉 자세한 내용은 README.md에서 \"윈도우 인코딩 해결\"을 참조해주세요.\n")
        print("⚠️ 경고 : 이 작업은 윈도우에서 킹갓 대한민국의 프로그램들의 한글이 정상적으로 표시되지 않을 수 있습니다.")
        # Pause
        input("계속하려면 Enter 키를 누르세요...")

        webbrowser.open('intl.cpl')

        print("👉 intl.cpl가 열렸습니다.\n")
        print("👉 관리자 옵션 -> 시스템 로켈 변경")
        print("👀 Beta: 세계 언어 지원을 위해 Unicode UTF-8 사용")
        print("👉 이 설정을 변경한 후, 시스템을 재시작하세요.\n")
        print("⚠️ 이 작업은 시스템 언어 설정을 변경하므로 주의가 필요합니다.\n")
        print("=======================================================")
        input("계속하려면 Enter 키를 누르세요...")
        

async def setup_user_data():
    print("\n📂 사용자 데이터 디렉토리를 설정하시겠습니까?")
    print("⚠️ 사용자 데이터 디렉토리는 브라우저의 프로필 데이터를 저장하는 곳입니다.")
    print("✅ 이 작업은 Google API Key를 설정하고 나서 진행해야만합니다.")
    if prompt_yes_no("\033[1m\033[33m선택하시려면 y를 입력하세요 (y/n):\033[0m "):
        if os.getenv("GOOGLE_API_KEY") is None:
            print("⚠️ Google API Key가 설정되어 있지 않습니다. 먼저 Google API Key를 설정해주세요.")
            return
        print("======================================================")
        llm = ChatGoogle(
            model="gemini-2.0-flash",
        )
        initial_actions = [
            {'go_to_url': {'url': 'https://www.google.com', 'new_tab': False}},
            {'wait': {'seconds': 2147483647}},
        ]

        agent = Agent(
            task="Just Wait",
            llm=llm,
            use_vision=False,
            initial_actions=initial_actions,
            browser_profile=BrowserProfile(
                disable_security=True,
                stealth=True,
                headless=False,
                device_scale_factor=1,
                window_size={"width": 1600, "height": 900},
                viewport={"width": 1600, "height": 900},
                user_data_dir="./data/user_data",
            )
        )
        
        print("======================================================\n")
        print("👉 브라우저가 열립니다. 필요한 로그인을 완료한 후 엔터키를 눌러 다음 단계로 진행하세요.")
        input("계속하려면 Enter 키를 누르세요...\n")
        print("======================================================")
        
        # 브라우저를 백그라운드에서 시작
        def run_agent():
            asyncio.run(agent.run())
        
        agent_thread = threading.Thread(target=run_agent)
        agent_thread.daemon = True
        agent_thread.start()
        
        # 사용자가 'n'을 입력할 때까지 대기
        while True:
            user_input = input("").strip().lower()
            if user_input == '':
                break

        print("======================================================")
        print("✅ 설정이 완료되었습니다.")
    else:
        print("🚫 설정이 취소되었습니다.")
    print("======================================================")
    print("⚠️ 이후에 USER_DATA_DIR을 설정하려면, .env 파일을 참고하여 USER_DATA_DIR을 설정하세요.\n")

def setup_sensitive():
    print("\n🔐 Sensitive Data을 설정하시겠습니까?")
    print("👉 이미 세션을 설정했다면, 이 작업은 **선택사항**입니다.")
    print("⚠️ 민감 정보 파일은 오류를 유발하거나 문제가 될 수 있으므로 가급적 세션 사용을 권장합니다.")
    if prompt_yes_no("\033[1m\033[33m선택하시려면 y를 입력하세요 (y/n):\033[0m "):
        print("======================================================")
        print("👀 .sensitive.json 파일을 생성합니다.")
        print("💾 Browser Use의 문서를 참조하여 수정을 수정해주세요.")
        print("https://docs.browser-use.com/customize/sensitive-data")
        create_file_from_example('.sensitive.json', '.sensitive.example.json')
        print("======================================================")
        print("✅ .sensitive.json 파일이 생성되었습니다.")
    else:
        print("🚫 .sensitive.json 생성이 취소되었습니다.")
    print("======================================================")
    print("⚠️ 이후에 민감 정보 파일을 설정하려면, .sensitive.example.json 파일을 참고하여 .sensitive.json 파일을 생성하세요.\n")

if __name__ == "__main__":
    # 1. .env 생성
    create_file_from_example('.env', '.env.example')
    print("=====================================================")
    # 2. Playwright용 Chrome 설치
    install_playwright_chrome()
    print("=====================================================")

    # 3. Windows 인코딩 문제 해결
    i_dont_like_windows()
    print("=====================================================")

    # 4. Setup User Data
    asyncio.run(setup_user_data())
    print("=====================================================")

    # 5. .sensitive.json 생성
    # setup_sensitive()
    print("=====================================================")
    print("🎉 초기 설정이 완료되었습니다! 이제 스크립트를 실행할 준비가 되었습니다.")
    print("🎉 초기 설정이 완료되었습니다! 이제 스크립트를 실행할 준비가 되었습니다.")
