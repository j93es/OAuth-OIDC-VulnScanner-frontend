import asyncio
from gc import disable
from logging import config
import zipfile
import requests
from dotenv import load_dotenv
from pathlib import Path
import shutil

from browser_use import Agent, Browser, BrowserConfig
from browser_use.browser.context import BrowserContextConfig

from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

UBLOCK_DIR = Path("./browser/ublock-origin")
TEMP_EXTRACT_DIR = Path("./browser/temp_ublock_extract")

def ensure_ublock_origin():
    if UBLOCK_DIR.exists() and (UBLOCK_DIR / "manifest.json").exists():
        print("✅ uBlock Origin already present.")
        return
    if not UBLOCK_DIR.parent.exists():
        UBLOCK_DIR.parent.mkdir(parents=True, exist_ok=True)

    print("⬇️ Downloading uBlock Origin from GitHub API...")

    # 1. GitHub API로 최신 릴리스 정보 가져오기
    api_url = "https://api.github.com/repos/gorhill/uBlock/releases/latest"
    res = requests.get(api_url)
    res.raise_for_status()
    data = res.json()

    # 2. assets 중 'uBlock0.chromium.zip' 찾기
    asset = next((a for a in data["assets"] if ".chromium.zip" in a["name"]), None)
    if not asset:
        raise Exception("❌ Could not find uBlock0.chromium.zip in GitHub release.")

    zip_url = asset["browser_download_url"]

    # 3. 다운로드
    zip_path = Path("./browser/ublock.zip")
    with requests.get(zip_url, stream=True) as r:
        r.raise_for_status()
        with open(zip_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    # 4. 압축 해제 후 내부 디렉터리 이동
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(TEMP_EXTRACT_DIR)

    # zip 안에 uBlock0.chromium/ 폴더가 있다고 가정
    extracted_root = next(TEMP_EXTRACT_DIR.iterdir())
    if extracted_root.name != "uBlock0.chromium":
        raise Exception("❌ Unexpected directory inside zip:", extracted_root)

    shutil.move(str(extracted_root), UBLOCK_DIR)

    shutil.rmtree(TEMP_EXTRACT_DIR, ignore_errors=True)
    zip_path.unlink()  # zip 삭제
    print("✅ uBlock Origin downloaded and extracted.")

ensure_ublock_origin()

browser = Browser(
    config=BrowserConfig(
        browser_type="chromium",
        headless=False,
        disable_security=True,

        extra_browser_args=[
            f"--load-extension={UBLOCK_DIR}",
            f"--disable-extensions-except={UBLOCK_DIR}",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
            "--disable-popup-blocking",
            
        ],
    )
)

async def main():
    agent = Agent(
        browser=browser,
        task="https://naver.com의 로그인 페이지를 찾아줘",
        llm=ChatGoogleGenerativeAI(model="gemini-2.0-flash"),
    )

    await agent.run()

asyncio.run(main())
