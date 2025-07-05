import os
import shutil
import tempfile

from lib.browser_use.func import *
from lib.utils.config import USER_DATA_DIR

# Initialize configuration
proxy_url = setup_proxy()


async def GetProfile(headless=False):
    user_data_dir = None
    if USER_DATA_DIR and os.path.isdir(USER_DATA_DIR):
        try:
            tmp_user_data_dir = tempfile.mkdtemp()
            if os.path.exists(tmp_user_data_dir):
                shutil.rmtree(tmp_user_data_dir)
            shutil.copytree(USER_DATA_DIR, tmp_user_data_dir, dirs_exist_ok=False, ignore_dangling_symlinks=True)
            user_data_dir = tmp_user_data_dir
            print(f"✅ Copied user data dir to temporary location: {user_data_dir}")
        except Exception as e:
            print(f"❌ Failed to copy user data dir: {e}")

    profile = BrowserProfile(
        # Security settings
        disable_security=True,
        #stealth=True,
        # Display settings
        headless=headless,
        device_scale_factor=1,
        window_size={"width": 1600, "height": 900},
        # Data persistence
        user_data_dir=user_data_dir,
        #storage_state=storage_state,
        # Network settings
        proxy={"server": proxy_url} if proxy_url else None,
        # Additional arguments
        args=get_browser_args(),
        ignore_default_args=['--enable-automation']
    )

    return profile
