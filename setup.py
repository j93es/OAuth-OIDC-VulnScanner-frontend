import os
import subprocess
import webbrowser

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
        

def setup_storage():
    print("\n🔧 쿠키와 로컬 스토리지를 설정하시겠습니까?")
    print("👀 다음 단계에서 Senstive Data를 설정할 수 있지만 쿠키와 로컬 스토리지를 더 권장합니다.")
    if prompt_yes_no("\033[1m\033[33m선택하시려면 y를 입력하세요 (y/n):\033[0m "):
        print("======================================================")
        print("👀 원하는 OAuth Providor를 직접 모두 로그인 한 후에 브라우저를 닫으면 설정이 완료됩니다.")
        os.system('uv run playwright open https://google.com/ --save-storage=./data/storage_state.json')
        print("✅ 쿠키와 로컬 스토리지 설정 완료.")
        print("💾 ./data/storage_state.json 파일이 생성되었습니다.")
    else:
        print("🚫 쿠키와 로컬 스토리지 설정이 취소되었습니다.")
    print("======================================================")
    print("⚠️ 이후에 쿠키와 로컬 스토리지를 설정하려면, `uv run playwright open https://google.com/ --save-storage=./data/storage_state.json` 명령어를 사용하세요.\n")


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

    # 4. 쿠키와 로컬 스토리지 설정
    setup_storage()
    print("=====================================================")

    # 5. .sensitive.json 생성
    setup_sensitive()
    print("=====================================================")
    print("🎉 초기 설정이 완료되었습니다! 이제 스크립트를 실행할 준비가 되었습니다.")
