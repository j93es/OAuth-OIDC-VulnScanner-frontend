from playwright.sync_api import sync_playwright

def launch_browser_with_profile():
    p = sync_playwright().start()
    browser = p.chromium.launch_persistent_context(
        user_data_dir="./data/user_data",
        headless=False
    )
    page = browser.new_page()
    return browser, page, p

if __name__ == "__main__":
    browser, page, playwright = launch_browser_with_profile()
    page.goto("https://example.com")
    print("Browser launched with user data profile.")
    
    # 브라우저가 열린 상태를 유지
    input("Press Enter to close the browser...")
    
    # 리소스 정리
    browser.close()
    playwright.stop()