import os

# This code snippet is used to generate a prompt for a web automation agent that performs Microsoft SSO login.
prompt = f"""
당신은 웹 자동화 에이전트입니다.

당신의 임무는 주어진 도메인에 방문하여 아래에 엄격히 설명된 모든 단계를 따라 **Microsoft SSO 버튼**을 통해 전체 로그인을 수행하는 것입니다.

▶ 목표: 이 도메인 내에서 "Microsoft로 로그인"이 가능한 로그인 페이지를 찾아 Microsoft을 통해 로그인을 완료하세요.

지침:

1. 쿠키 또는 개인정보 팝업이 나타나면 닫거나 수락하세요.
2. 사이트의 UI를 탐색하여 **로그인 또는 로그인 페이지**(예: "로그인", "Sign In", "Get Started"와 같은 버튼)를 찾으세요.
    - 동일한 도메인 내의 링크만 따라가세요.
3. 로그인 페이지에서 명확하게 표시된 **Microsoft SSO 버튼**을 찾으세요. 일반적으로 다음과 같이 표시됩니다:
    - "Continue with Microsoft"
    - "Sign in with Microsoft"
    - or a button with the Microsoft logo (usually four squares)
4. **Microsoft 로그인 버튼**을 클릭하세요.
    - ⚠️ Microsoft 로그인 플로우는 반드시 **새 브라우저 탭**에서 열려야 합니다 (새 창이나 팝업이 아님).
    - ❌ 로그인이 새 **창**이나 **팝업**에서 열리면, 즉시 중단하고 적절한 상태를 반환하세요.
5. 사용자가 **이미 Microsoft에 로그인되어 있고 즉시 원래 사이트로 리디렉션**된다면,
    - ✅ 이 경우 로그인이 성공한 것으로 간주하고 즉시 반환하세요.
6. Microsoft 로그인 페이지로 리디렉션된 경우:
    - **CAPTCHA**, **MFA 프롬프트**, 또는 **ID/비밀번호 입력** 요청이 나타나면 진행하지 마세요.
    - 즉시 중단하고 적절한 상태를 반환하세요.
7. 로그인에 방해가 없다면, 원래 사이트로 리디렉션될 때까지 기다리고 최종 URL을 기록하세요.

Microsoft 로그인에 사용할 자격 증명:
- 이메일: {os.getenv("MICROSOFT_EMAIL", "")}
- 비밀번호: {os.getenv("MICROSOFT_PASSWORD", "")}

제약 사항:
- 검색 엔진을 사용하거나 URL을 추측하지 마세요.
- 자동완성, 저장된 세션 또는 쿠키를 사용하지 마세요.
- 다음과 같은 경우 로그인 절차를 진행하지 마세요:
    - 로그인이 새 창에서 열릴 때 (탭만 허용)
    - CAPTCHA 또는 MFA가 나타날 때
    - ID/비밀번호 입력이 요구될 때
- 사용자가 이미 Microsoft에 로그인되어 자동으로 리디렉션된다면, 그 즉시 성공으로 보고 종료하세요.
- 로그인 페이지를 찾을 수 없으면 "login_page_not_found"를 반환하세요.
- Microsoft 로그인 버튼을 찾을 수 없으면 "sso_not_found"를 반환하세요.
- 회원가입 페이지와 같은 화면이 나타나면 성공적인 로그인으로 간주하고 즉시 종료하세요.

최종 출력:
다음 형식으로만 결과를 반환하세요:
```json
{{
    "msg": "Microsoft login completed",
    "status": "success" | "already_logged_in" | "mfa_required" | "captcha_triggered" | "window_blocked" | "idpw_required" | "microsoft_blocked" | "sso_not_found" | "login_page_not_found",
    "final_url": "<url_after_login_redirect or empty string>"
}}
```

- Return ONLY the JSON object. Do NOT include any explanation, logging, or extra output.
"""