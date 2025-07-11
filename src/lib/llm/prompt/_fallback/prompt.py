from dotenv import load_dotenv
import os

load_dotenv()
google_id = os.getenv("GOOGLE_ID")
google_password = os.getenv("GOOGLE_PASSWORD")

naver_id = os.getenv("NAVER_ID")
naver_password = os.getenv("NAVER_PASSWORD")

facebook_id = os.getenv("FACEBOOK_ID")
facebook_password = os.getenv("FACEBOOK_PASSWORD")

github_id = os.getenv("GITHUB_ID")
github_password = os.getenv("GITHUB_PASSWORD")

microsoft_id = os.getenv("MICROSOFT_ID")
microsoft_password = os.getenv("MICROSOFT_PASSWORD")

# Extended planner prompt
prompt = f"""
You are a web automation agent.

Your task is to visit the given domain and perform a full login via the **SSO Login button**, following all steps strictly as described below.

Instructions:

1. If any cookie or privacy popups appear, dismiss or accept them.
2. Navigate through the site's UI to find the **login or sign-in page** (e.g., via buttons like "Log In", "Sign In", "Get Started").
3. Click the **SSO login button**.
4. Check if the user is **already logged and immediately redirected back to the original site** without showing a login screen.
    - ✅ If so, treat the login as successful and return immediately.
5. If login proceeds without interruptions, complete the login and **immediately close the browser window**. Do not perform any further actions.
6. Login is considered successful if:
    - You are redirected to a page that indicates successful login (e.g., a welcome page, dashboard, or account page).
    - If a page such as a sign-up page appears, consider it a successful login and terminate immediately.
    
Credentials to use for login:
- Google → `{google_id}` / `{google_password}`
- Naver → `{naver_id}` / `{naver_password}`
- GitHub → `{github_id}` / `{github_password}`
- facebook → `{facebook_id}` / `{facebook_password}`
- Microsoft → `{microsoft_id}` / `{microsoft_password}`

Constraints:
- Do NOT use search engines or guess URLs.
- Do NOT proceed with login if:
    - CAPTCHA or MFA appears
- If the user is already logged and redirected back automatically, stop there and report success.
- If the login page cannot be found, return "login_page_not_found".
- If the login button is not found, return "sso_not_found".
- If a page such as a sign-up page appears, consider it a successful login and terminate immediately.

Final Output:
Return the result in the following format only:

```json
{{
    "msg": "login completed",
    "status": "success" | "already_logged_in" | "mfa_required" | "captcha_triggered" | "window_blocked" | "idpw_required" | "sso_not_found" | "login_page_not_found",
    "final_url": "<url_after_login_redirect or empty string>"
}}
```

- Return ONLY the JSON object. Do NOT include any explanation, logging, or extra output.
"""
