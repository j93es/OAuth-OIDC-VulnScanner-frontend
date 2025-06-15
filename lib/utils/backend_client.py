import requests
from config import BACKEND_URL

def notify_backend(target_url):
    # Backend에 스캔 시작을 알림
    try:
        response = requests.post(
            f"{BACKEND_URL}/start", params={"url": target_url}, timeout=5
        )
        if response.status_code == 200:
            print(f"✅ Backend notified: {response.text}")
        else:
            print(f"⚠️ Backend notification failed: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(
            f"⚠️ Backend server not available at {BACKEND_URL}. Continuing without notification."
        )
    except requests.exceptions.Timeout:
        print(f"⚠️ Backend notification timed out. Continuing without notification.")
    except Exception as e:
        print(f"⚠️ Failed to notify backend: {e}")
