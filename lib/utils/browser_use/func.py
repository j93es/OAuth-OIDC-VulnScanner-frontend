import os
import json
from pathlib import Path
from dotenv import load_dotenv
from browser_use import BrowserProfile

# Load environment variables
load_dotenv(override=True)

def safe_json_read(file_path: Path) -> dict:
    """Safely read JSON file with proper encoding handling."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (UnicodeDecodeError, json.JSONDecodeError):
        # Try with different encodings
        for encoding in ['utf-8-sig', 'latin1', 'cp1252']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return json.load(f)
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
    return {}

def safe_json_write(file_path: Path, data: dict):
    """Safely write JSON file with proper encoding handling."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


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

            # 안전한 JSON 파일 처리 (인코딩 문제 해결)
            storage_data = safe_json_read(storage_state_path)
            
            if storage_data:  # 데이터가 성공적으로 읽혔다면
                safe_json_write(storage_state_temp_path, storage_data)
                print(f"🔄 Using existing storage state: {storage_state_temp_path}")
                return str(storage_state_temp_path)
            else:
                print("⚠️ Storage state file is empty or corrupted")
                return None
                
        except Exception as e:
            print(f"⚠️ Error processing storage state: {e}")
            # 문제가 있는 파일을 제거하고 새로 시작
            if storage_state_temp_path.exists():
                storage_state_temp_path.unlink()
            return None

    print("⚠️ No existing storage state found")
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

def cleanup_corrupted_storage_files():
    """Clean up corrupted storage state files."""
    script_dir = Path(__file__).parent.parent.parent.parent
    storage_state_temp_path = script_dir / "data" / "storage_state_temp.json"
    
    if storage_state_temp_path.exists():
        try:
            # Try to read the file to check if it's corrupted
            with open(storage_state_temp_path, 'r', encoding='utf-8') as f:
                json.load(f)
            print(f"✅ Storage temp file is valid: {storage_state_temp_path}")
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            print(f"🗑️ Removing corrupted storage temp file: {e}")
            storage_state_temp_path.unlink()

