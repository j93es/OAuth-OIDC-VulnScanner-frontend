import os
from pathlib import Path
from dotenv import load_dotenv
from browser_use import BrowserProfile

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


def setup_storage_state():
    """Setup browser storage state for session persistence."""
    storage_state_path = Path("./data/storage_state.json").resolve()
    storage_state_temp_path = Path("./data/storage_state_temp.json").resolve()

    if storage_state_path.exists():
        if storage_state_temp_path.exists():
            storage_state_temp_path.unlink()

        storage_state_temp_path.write_text(
            storage_state_path.read_text(encoding="utf-8"), encoding="utf-8"
        )
        print(f"🔄 Using existing storage state: {storage_state_temp_path}")
        return str(storage_state_temp_path)

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
