import os
import shutil
import tempfile

from lib.browser_use.func import *
from lib.utils.config import USER_DATA_DIR

# Initialize configuration
proxy_url = setup_proxy()


async def GetProfile(headless=False):
    user_data_dir = None
    tmp_user_data_dir = None
    if USER_DATA_DIR and os.path.isdir(USER_DATA_DIR):
        try:
            tmp_user_data_dir = tempfile.mkdtemp()
            # write path in user_data_dir_path
            print(f"🔧 Using user data dir: {USER_DATA_DIR}")
            print(f"🔧 Temporary user data dir: {tmp_user_data_dir}")

            log_file = os.path.join("./data", "userdata.dump")
            if not os.path.exists("./data"):
                os.makedirs("./data")
            if os.path.exists(log_file):
                os.remove(log_file)
            
            # Log current browser use directory
            with open(log_file, "w") as f:
                f.write(f"{tmp_user_data_dir}")

            # Copy USER_DATA_DIR to tmp_user_data_dir
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
        #device_scale_factor=1,
        #window_size={"width": 1600, "height": 900},
        #viewport={"width": 1600, "height": 900},
        # Data persistence
        user_data_dir=user_data_dir,
        #storage_state=storage_state,
        # Network settings
        proxy={"server": proxy_url} if proxy_url else None,
        # Additional arguments
        #args=get_browser_args(),
        ignore_default_args=['--enable-automation', '--disable-extensions', '--hide-scrollbars', '--disable-features=AcceptCHFrame,AutoExpandDetailsElement,AvoidUnnecessaryBeforeUnloadCheckSync,CertificateTransparencyComponentUpdater,DeferRendererTasksAfterInput,DestroyProfileOnBrowserClose,DialMediaRouteProvider,ExtensionManifestV2Disabled,GlobalMediaControls,HttpsUpgrades,ImprovedCookieControls,LazyFrameLoading,LensOverlay,MediaRouter,PaintHolding,ThirdPartyStoragePartitioning,Translate'],
    )

    return [profile, tmp_user_data_dir] if tmp_user_data_dir else [profile]
