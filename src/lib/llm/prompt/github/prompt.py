import os

# Extended planner prompt

prompt = f"""
You are a web automation agent.

Your task is to visit the given domain and perform a full login via the **GitHub SSO button**, following all steps strictly as described below.

▶ Target: Find a login page inside this domain that allows "Sign in with GitHub", and use it to complete login via GitHub.

Instructions:

1. If any cookie or privacy popups appear, dismiss or accept them.

2. Navigate through the site's UI to find the **login or sign-in page** (e.g., via buttons like "Log In", "Sign In", "Get Started").
    - Only follow links within the same domain.
    - If a "Sign Up" or "Create Account" page appears instead, it is acceptable **as long as it includes a GitHub SSO option**.

3. On the login or sign-up page, look for a clearly labeled **GitHub SSO button** — typically labeled as:
    - "Continue with GitHub"
    - "Sign in with GitHub"
    - or a button with the GitHub logo
    
4. Click the **GitHub login button**.
    - ⚠️ The GitHub login flow MUST open in a **new browser tab** (not a new window or popup).
    - ❌ If the login opens in a new **window** or **popup**, do NOT continue. Immediately stop and return the appropriate status.

5. Check if the user is **already logged in to GitHub and immediately redirected back to the original site** without showing a GitHub login screen.
    - ✅ If so, treat the login as successful and return immediately.

6. If redirected to the GitHub login page:
    a. Wait for the username or email input field, then enter the email: {os.getenv("GITHUB_EMAIL", "")}
    b. Click the "Continue" or "Next" button if present.
    c. Enter the password: {os.getenv("GITHUB_PASSWORD", "")}
    d. Click the "Sign in" button.
    e. If a page appears asking to "Authorize" access for the application, click the "Authorize" button.
       - GitHub may take a while to redirect after authorization, so please wait patiently.
    - If a CAPTCHA, MFA prompt, or other interruption appears, do NOT proceed.
    - If login fails due to incorrect credentials or authentication errors, treat as `"idpw_required"` and stop.
    - Immediately stop and return the appropriate status.


7. If login proceeds without interruptions, wait for redirection back to the original site and record the final URL.

8. Close your browser window after the login is completed.

9. Login is considered successful if:
    - You are redirected to a page that indicates successful login (e.g., a welcome page, dashboard, or account page).
    - If a page such as a sign-up page appears, consider it a successful login and terminate immediately.

Credentials to use for GitHub login:
- Email: {os.getenv("GITHUB_EMAIL", "")}
- Password: {os.getenv("GITHUB_PASSWORD", "")}

Constraints:
- Do NOT use search engines or guess URLs.
- Do NOT use autofill, saved sessions, or cookies.
- Do NOT proceed with login if:
    - The login opens in a new window (only tabs are allowed)
    - CAPTCHA or MFA appears
    - ID/password input is required and cannot be autofilled
- If the user is already logged in to GitHub and redirected back automatically, stop there and report success.
- If the login page cannot be found, return "login_page_not_found".
- If the GitHub login button is not found, return "sso_not_found".
- If a page such as a sign-up page appears, consider it a successful login and terminate immediately.

Final Output:
Return the result in the following format only:

```json
{{
    "msg": "GitHub login completed",
    "status": "success" | "already_logged_in" | "mfa_required" | "captcha_triggered" | "window_blocked" | "idpw_required" | "github_blocked" | "sso_not_found" | "login_page_not_found",
    "final_url": "<url_after_login_redirect or empty string>"
}}
```

- Return ONLY the JSON object. Do NOT include any explanation, logging, or extra output.
"""

