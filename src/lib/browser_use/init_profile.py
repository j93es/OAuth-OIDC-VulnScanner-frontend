import os

from lib.browser_use.func import *

# Initialize configuration
proxy_url = setup_proxy()


async def GetProfile():
    storage_state_path = await setup_storage_state()

    # Handle potential encoding issues with storage state file
    try:
        if storage_state_path and os.path.exists(storage_state_path):
            # Test if file can be read properly, if not, skip it
            with open(storage_state_path, "r", encoding="utf-8") as f:
                f.read()
            storage_state = storage_state_path
        else:
            print(
                "⚠️ Storage state file not found or inaccessible, proceeding without it."
            )
            storage_state = None
    except (UnicodeDecodeError, FileNotFoundError):
        # If there's an encoding error, don't use the storage state
        storage_state = None

    profile = BrowserProfile(
        # Security settings
        disable_security=True,
        stealth=True,
        # Display settings
        headless=False,
        device_scale_factor=1,
        window_size={"width": 1600, "height": 900},
        viewport={"width": 1600, "height": 900},
        # Data persistence
        user_data_dir=None,
        storage_state=storage_state,
        # Network settings
        proxy={"server": proxy_url} if proxy_url else None,
        # Additional arguments
        args=get_browser_args(),
    )

    return profile
