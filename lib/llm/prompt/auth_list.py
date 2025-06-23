# @file purpose: This file contains the prompt for extracting a list of OAuth providers from a web page.
# OAuth 리스트 추출용 프롬프트 (클릭하지 않고 단순 식별만)
extract_oauth_list_prompt = f"""
🎯 목적: 주어진 초기 URL 내에서 **OAuth 로그인 Provider**를 찾아 아래 형식의 JSON으로 정리합니다.

📌 작업 목표:
- Google, GitHub, Discord, Facebook, Apple, Microsoft, Twitter, LinkedIn 등 **OAuth 인증을 사용하는 외부 로그인 링크**에서 Provider 이름만 모두 수집합니다.
- 로그인 버튼, 링크 클릭 등을 통해 탐색을 진행할 수 있습니다.
- **같은 provider가 여러 번 나와도 하나만 저장**합니다.

🛑 제한 사항:
- ❌ 로그인 입력창이나 이메일/비밀번호 입력 방식은 제외합니다.
- ❌ 검색 엔진, 사이트 외부 탐색은 금지합니다.

🔍 탐색 방법:
1. 초기 URL에 접속하여 **클라이언트용 로그인 페이지**로 진입합니다.
2. 페이지가 정상적으로 로드되었다고 가정합니다.
3. 'Continue with X', 'Continue with Google'... 등의 버튼이나 링크를 식별합니다.


🧾 출력 형식 (예시):

```json
{{
  "oauth_providers": [
    "Google",
    "GitHub",
    "Discord"
  ]
}}
```

📌 주의:
    결과가 없는 경우 빈 배열 `[]`로 반환합니다.
    정확한 provider 이름을 포함해 주세요.

"""

