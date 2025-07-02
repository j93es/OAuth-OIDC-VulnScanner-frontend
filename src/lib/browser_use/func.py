import json
import os
from pathlib import Path

from browser_use import BrowserProfile
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)


async def setup_storage_state():
    """Setup browser storage state for session persistence."""
    # Get the script directory to ensure correct path resolution
    script_dir = Path(__file__).parent.parent.parent.parent
    storage_state_path = script_dir / "data" / "storage_state.json"
    storage_state_temp_path = script_dir / "data" / "storage_state_temp.json"

    print(f"📂 Storage state path: {storage_state_path}")
    print(f"📂 Temp storage state path: {storage_state_temp_path}")

    if storage_state_path.exists():
        try:
            if storage_state_temp_path.exists():
                storage_state_temp_path.unlink()

            with open(storage_state_path, "r") as f:
                storage_data = json.load(f)

            with open(storage_state_temp_path, "w") as f:
                json.dump(storage_data, f, indent=4)

            print(f"🔄 Using existing storage state: {storage_state_temp_path}")
            return str(storage_state_temp_path)

        except Exception as e:
            print(f"⚠️ Error processing storage state: {e}")
            if storage_state_temp_path.exists():
                storage_state_temp_path.unlink()
            return None

    print("⚠️ No existing storage state found")
    return None


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
