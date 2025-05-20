from browser_use.browser.context import BrowserContextConfig
from pathlib import Path
import os

from typing import Any

def browser_config_kwargs(lang: str = "en_US") -> dict[str, Any]:
    browser_config_kwargs: dict[str, Any] = {
        "keep_alive": True,
        "browser_type": "chromium",
        "headless": False,
        "disable_security": True,
        "extra_browser_args": [
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
            "--disable-popup-blocking",
            f"--lang={lang}",
        ],
    }

    proxy_host = os.getenv("PROXY_HOST")
    proxy_port = os.getenv("PROXY_PORT")
    if proxy_host and proxy_port:
        browser_config_kwargs["proxy"] = {"server": f"http://{proxy_host}:{proxy_port}"}

    return browser_config_kwargs