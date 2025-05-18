import asyncio
from locale import locale_alias
from dotenv import load_dotenv
from browser_use import Agent, Browser, BrowserConfig
from browser_use.browser.context import BrowserContextConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_text_splitters import Language
from lib.ublock_init import ensure_ublock_origin
from pathlib import Path
import os

load_dotenv()

UBLOCK_DIR = Path("./browser/ublock-origin")

ensure_ublock_origin(UBLOCK_DIR)

browser = Browser(
    config=BrowserConfig(
        browser_type="chromium",
        headless=False,
        disable_security=True,
        proxy={"server": f"http://{os.getenv('PROXY_HOST')}:{os.getenv('PROXY_PORT')}"},

        extra_browser_args=[
            f"--load-extension={UBLOCK_DIR}",
            f"--disable-extensions-except={UBLOCK_DIR}",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
            "--disable-popup-blocking",
            "--lang=en-US",
        ],
        context=BrowserContextConfig(
            locale="en-US",
            # You can also set 'accept_language' if supported:
            accept_language="en-US,en"
        ),
    )
)

async def main():
    agent = Agent(
        browser=browser,
        task="http://naver.com의 로그인 페이지를 찾아줘",
        llm=ChatGoogleGenerativeAI(model="gemini-2.0-flash"),
    )

    await agent.run()

asyncio.run(main())
