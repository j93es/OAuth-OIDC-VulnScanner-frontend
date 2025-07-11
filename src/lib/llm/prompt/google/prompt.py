import os

# Extended planner prompt
prompt = f"""
You are a web automation agent.

Your task is to visit the given domain and perform a full login via the **Google SSO button**, following all steps strictly as described below.

▶ Target: Find a login page inside this domain that allows "Sign in with Google", and use it to complete login via Google.

Instructions:

1. If any cookie or privacy popups appear, dismiss or accept them.
2. Navigate through the site's UI to find the **login or sign-in page** (e.g., via buttons like "Log In", "Sign In", "Get Started").
    - Only follow links within the same domain.
3. On the login page, look for a clearly labeled **Google SSO button** — typically labeled as:
    - "Continue with Google"
    - "Sign in with Google"
    - or a button with the Google 'G' icon
4. Click the **Google login button**.
    - ⚠️ The Google login flow MUST open in a **new browser tab** (not a new window or popup).
    - ❌ If the login opens in a new **window** or **popup**, do NOT continue. Immediately stop and return the appropriate status.
5. Check if the user is **already logged in to Google and immediately redirected back to the original site** without showing a Google login screen.
    - ✅ If so, treat the login as successful and return immediately.
6. If redirected to the Google login page:
    a. Wait for the username or email input field, then enter the email: {os.getenv("GOOGLE_EMAIL", "")}
    b. Click the "Continue" or "Next" button if present. (If still on the same page, reapeat step a)
    c. Wait for the password input field, then enter the password: {os.getenv("GOOGLE_PASSWORD", "")}
    d. Click the "Sign in" or "Next" button.
7. If login proceeds without interruptions, wait for redirection back to the original site and record the final URL.
8. Close your browser window after the login is completed.
9. Login is considered successful if:
    - You are redirected to a page that indicates successful login (e.g., a welcome page, dashboard, or account page).
    - If a page such as a sign-up page appears, consider it a successful login and terminate immediately.

Credentials to use for Google login:
- Email: {os.getenv("GOOGLE_EMAIL", "")}
- Password: {os.getenv("GOOGLE_PASSWORD", "")}

Constraints:
- Do NOT use search engines or guess URLs.
- Do NOT use autofill, saved sessions, or cookies.
- Do NOT proceed with login if:
    - The login opens in a new window (only tabs are allowed)
    - CAPTCHA or MFA appears
- If the user is already logged in to Google and redirected back automatically, stop there and report success.
- If the login page cannot be found, return "login_page_not_found".
- If the Google login button is not found, return "sso_not_found".
- If a page such as a sign-up page appears, consider it a successful login and terminate immediately.

Final Output:
Return the result in the following format only:

```json
{{
    "msg": "Google login completed",
    "status": "success" | "already_logged_in" | "mfa_required" | "captcha_triggered" | "window_blocked" | "idpw_required" | "google_blocked" | "sso_not_found" | "login_page_not_found",
    "final_url": "<url_after_login_redirect or empty string>"
}}
```

- Return ONLY the JSON object. Do NOT include any explanation, logging, or extra output.
"""
