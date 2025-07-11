import os
import shutil
import tempfile

from lib.browser_use.func import *
from lib.utils.config import USER_DATA_DIR

# Initialize configuration
proxy_url = setup_proxy()


async def GetProfile(headless=False):
    """브라우저 프로필을 생성하고 임시 사용자 데이터 디렉토리를 관리합니다."""
    user_data_dir = None
    tmp_user_data_dir = None
    
    if USER_DATA_DIR and os.path.isdir(USER_DATA_DIR):
        try:
            tmp_user_data_dir = tempfile.mkdtemp(prefix="browser_use_")
            print(f"🔧 기본 사용자 데이터 디렉토리: {USER_DATA_DIR}")
            print(f"🔧 임시 사용자 데이터 디렉토리: {tmp_user_data_dir}")

            log_file = os.path.join("./data", "userdata.dump")
            if not os.path.exists("./data"):
                os.makedirs("./data")
                
            # 기존 로그 파일이 있다면 해당 디렉토리 정리
            if os.path.exists(log_file):
                try:
                    with open(log_file, "r") as f:
                        old_tmp_dir = f.read().strip()
                    if old_tmp_dir and os.path.exists(old_tmp_dir):
                        shutil.rmtree(old_tmp_dir)
                        print(f"🗑️ 이전 임시 디렉토리 정리: {old_tmp_dir}")
                except Exception as e:
                    print(f"⚠️ 이전 임시 디렉토리 정리 실패: {e}")
                os.remove(log_file)
            
            # 새 임시 디렉토리 경로 로깅
            with open(log_file, "w") as f:
                f.write(tmp_user_data_dir)

            # 사용자 데이터 디렉토리 복사
            if os.path.exists(tmp_user_data_dir):
                shutil.rmtree(tmp_user_data_dir)
            shutil.copytree(
                USER_DATA_DIR, 
                tmp_user_data_dir, 
                dirs_exist_ok=False, 
                ignore_dangling_symlinks=True
            )
            user_data_dir = tmp_user_data_dir
            print(f"✅ 사용자 데이터 디렉토리 복사 완료: {user_data_dir}")
        except Exception as e:
            print(f"❌ 사용자 데이터 디렉토리 복사 실패: {e}")
            # 실패 시 임시 디렉토리 정리
            if tmp_user_data_dir and os.path.exists(tmp_user_data_dir):
                try:
                    shutil.rmtree(tmp_user_data_dir)
                except Exception:
                    pass
            tmp_user_data_dir = None
            user_data_dir = None

    profile = BrowserProfile(
        # Security settings
        disable_security=True,
        # Display settings
        headless=headless,
        # Data persistence
        user_data_dir=user_data_dir,
        # Network settings
        proxy={"server": proxy_url} if proxy_url else None,
        # Additional arguments
        ignore_default_args=[
            '--enable-automation', 
            '--disable-extensions', 
            '--hide-scrollbars', 
            '--disable-features=AcceptCHFrame,AutoExpandDetailsElement,AvoidUnnecessaryBeforeUnloadCheckSync,CertificateTransparencyComponentUpdater,DeferRendererTasksAfterInput,DestroyProfileOnBrowserClose,DialMediaRouteProvider,ExtensionManifestV2Disabled,GlobalMediaControls,HttpsUpgrades,ImprovedCookieControls,LazyFrameLoading,LensOverlay,MediaRouter,PaintHolding,ThirdPartyStoragePartitioning,Translate'
        ],
    )

    return [profile, tmp_user_data_dir] if tmp_user_data_dir else [profile]
