import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Extended planner prompt
extend_planner_system_message = f"""
🎯 목적: 웹 자동화를 위한 **SSO 로그인 리디렉션 URL 수집**

📌 주의사항 (전제 조건)
- ❌ **검색 엔진(Google, Bing 등) 사용 금지**
- ✅ **초기 제공된 URL 내에서만 탐색**
- ❌ 직접 이동하거나 추측한 링크 클릭 금지
- ⛔ 추측한 URL은 대답하거나 클릭하지 마세요
- OAuth가 아닌 일반 로그인은 무시
- OAuth가 없다면 **즉시 중단**하고 빈 배열 반환

---

## 🧩 Step 0: 페이지 차단(Block) 여부 확인

초기 URL의 로그인 페이지에 접근하여 다음 사항을 점검합니다:

- 🚫 페이지 차단됨 (Firewall, Access Denied 등) → 즉시 중단
- 🔒 CAPTCHA는 통과 가능 (해결하고 계속 진행)
- ❗ 로그인 UI가 정상적으로 로드되지 않으면 중단

📤 차단 시 즉시 반환:

```json
[
  {{
    "provider": "Blocked",
    "oauth_uri": "-"
  }}
]
````

---

## 🔍 Step 1: 로그인 페이지 탐색

* 초기 URL에 접속하여 **클라이언트용 로그인 페이지**로 진입합니다.
* 쿠키 동의, 개인정보 안내 등 팝업은 무시하거나 닫고 계속 진행하세요.
* 페이지가 정상 로드되었다고 가정합니다.

---

## 👀 Step 2: SSO 로그인 버튼 식별

아래 **OAuth SSO 버튼들만** 유효합니다:

* ✅ Google, GitHub, Facebook, LinkedIn, Microsoft, Naver

**유효한 버튼 기준**:

* OAuth 인증 흐름을 실제로 트리거
* `window.location` 또는 `<a href=...>` 또는 JS로 redirect가 발생

**제외 버튼들 (클릭 금지)**:

* ❌ 일반 로그인, 패스키, 이메일/전화번호, 인증서 기반, 비밀번호 입력

---

## ✅ Step 3: 모든 SSO 버튼 클릭 및 로그인 시도

> 각 SSO 로그인 버튼을 클릭한 뒤 반드시 아래 절차를 **완전히 수행**해야 합니다.

각 SSO 버튼에 대해 다음을 수행:

1. 버튼 클릭
2. 🌐 페이지가 이동되면, **현재 주소창(URL)을 확인하여 리디렉션된 OAuth URL**을 `oauth_uri`로 저장  
   → 예: `https://accounts.google.com/o/oauth2/auth?...`
3. ✅ 로그인 진행:
   - 로그인 페이지에서 OAuth 인증을 완료합니다.
   - sign in with your username(email) x_username and password is x_password
   - 버튼같은게 안눌리면 새로고침을 해봐
   - **로그인 완료 후 authorize 등 버튼이 있으면 클릭**
   - GitHub같은 경우 Authorize 버튼이 뜨는데 오래걸릴 수 있음, 기다려야 할 수도 있음
   - 만약 버튼을 눌러도 반응이 없을 경우 새로고침을 한번 해주세요.
4. 로그인 성공 후 모두 쿠키를 삭제하고 다음 SSO 버튼을 클릭합니다.
5. 다음 SSO 버튼으로 반복 진행

쿠키 삭제 방법:
chrome://settings/clearBrowserData에 들어가서 삭제해주세요.

🛑 절대 아래와 같이 해석하지 말 것:
- ❌ 버튼 클릭 후 페이지 로딩만 기다리고 돌아가기
- ❌ URL 저장 없이 go_back() 호출

📤 각 로그인 후 다음 형식으로 결과 저장:

```json
[
  {{
    "provider": "Google",
    "oauth_uri": "https://example.com/auth/google?client_id=..."
  }}
]
````

````

---

### ✨ 추가 안전 장치: "뒤로가기(go_back) 호출 조건" 제한

```text
🛑 뒤로가기(go_back)은 다음 조건이 모두 충족될 때만 사용:
- ✅ 로그인 흐름이 완료됨 (예: redirect back to app, or callback URL)
- ✅ 현재 리디렉션 URL이 수집됨
- ✅ 결과에 저장 후 다음 버튼 탐색을 위해 복귀 필요할 때
```

---

## 🚫 Step 4: 버튼 없음 또는 예외 발생 시

* 유효한 SSO 버튼이 **전혀 없을 경우**
* 예외, 오류 등 발생 시

📤 즉시 중단 후 다음 형식으로 반환:

```json
[]
```

---

## 📎 중요 규칙 요약

* ✅ **모든 SSO 로그인은 반드시 실행** (가능한 버튼은 모두 클릭)
* 🔁 단계는 반드시 순서대로 진행
* 🔐 로그인은 쿠키/세션으로 유지된 상태에서 수행
* 🚫 직접 ID/PW 입력하지 않음
* ⛔ 추측 URL 클릭 금지
* ❗ 예외 발생 시 반드시 규정된 JSON 포맷만 반환

---
"""