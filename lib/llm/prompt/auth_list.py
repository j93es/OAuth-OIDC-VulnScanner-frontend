# OAuth 리스트 추출용 프롬프트 (클릭하지 않고 단순 식별만)
extract_oauth_list_prompt = f"""
🎯 목적: 로그인 페이지에서 **OAuth 제공자 리스트 추출**

📌 주요 규칙:
- ❌ **OAuth 버튼을 클릭하지 마세요**
- ✅ **OAuth 제공자만 식별하고 리스트 작성**
- ❌ 일반 로그인은 무시
- ❌ 검색 엔진 사용 금지

---

## 🔍 Step 1: 로그인 페이지 접근

* 초기 URL에 접속하여 **클라이언트용 로그인 페이지**로 진입합니다.
* 쿠키 동의, 팝업 등은 무시하거나 닫고 계속 진행하세요.

---

## 👀 Step 2: OAuth 제공자 식별

아래 **OAuth SSO 버튼들만** 식별합니다:

**유효한 OAuth 제공자들**:
* ✅ Google, GitHub, Facebook, LinkedIn, Microsoft, Naver, Kakao, Apple, Twitter/X
* ✅ "Continue with..." 또는 "Sign in with..." 버튼들
* ✅ OAuth 아이콘이 있는 버튼들

**제외할 항목들**:
* ❌ 일반 로그인 (이메일/비밀번호 입력)
* ❌ 패스키 (Passkey)
* ❌ 전화번호 인증
* ❌ 인증서 기반 로그인

---

## 📝 Step 3: 결과 반환

발견된 OAuth 제공자들을 다음 형식으로 반환:

```json
{{
  "oauth_providers": [
    {{
      "provider": "Google",
      "oauth_uri": ""
    }},
    {{
      "provider": "GitHub", 
      "oauth_uri": ""
    }}
  ]
}}
```

⚠️ **중요**: 버튼을 클릭하지 마세요. 단순히 식별만 하면 됩니다.
"""

