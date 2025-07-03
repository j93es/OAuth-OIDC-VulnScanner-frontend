import json
import os
from pathlib import Path

from browser_use import BrowserProfile
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)


def setup_proxy():
    """Configure proxy settings from environment variables."""
    proxy_host = os.getenv("PROXY_HOST")
    proxy_port = os.getenv("PROXY_PORT")

    if proxy_host and proxy_port:
        proxy_url = f"http://{proxy_host}:{proxy_port}"
        print(f"🔗 Using proxy: {proxy_host}:{proxy_port}")
        return proxy_url
    else:
        print("🔗 No proxy configured, using direct connection.")
        return None


def get_browser_args():
    """Get browser arguments for enhanced compatibility and security."""
    return [
        # Security and isolation
        "--disable-web-security",
        "--disable-site-isolation-trials",
        "--disable-features=IsolateOrigins,site-per-process",
        "--ignore-certificate-errors",
        "--ignore-ssl-errors",
        "--allow-running-insecure-content",
        # Performance and rendering
        "--disable-features=VizDisplayCompositor",
        "--disable-dev-shm-usage",
        # Popup and automation
        "--disable-popup-blocking",
        "--disable-blink-features=AutomationControlled",
        # Browser behavior
        "--no-first-run",
        "--no-service-autorun",
        "--no-default-browser-check",
        "--password-store=basic",
        "--use-mock-keychain",
        # Extensions
        "--disable-extensions-file-access-check",
        "--disable-extensions-http-throttling",
        "--disable-component-extensions-with-background-pages",
        # Language
        f"--lang={os.getenv('LANG', 'en_US')}",
    ]
