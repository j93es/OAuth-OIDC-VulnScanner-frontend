from func import *
import clean_resources as clean_resources_func

# Initialize configuration
proxy_url = setup_proxy()
storage_state_path = setup_storage_state()

# Create browser profile
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
    storage_state=storage_state_path,
    
    # Network settings
    proxy={"server": proxy_url} if proxy_url else None,
    
    # Additional arguments
    args=get_browser_args(),
)