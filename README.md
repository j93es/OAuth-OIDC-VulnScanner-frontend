# 환경 설정

요구 사항
- [uv](https://docs.astral.sh/uv/getting-started/installation/) - Python Package Manager Written by Rust
- [oauth-backend](https://github.com/j93es/oauth-backend)
- [Google Chrome](https://www.google.com/intl/ko_kr/chrome/)

---

> [oauth-backend](https://github.com/j93es/oauth-backend) 프록시를 사용한다면 이 가이드에 따라 인증서 또한 설정되어야만 합니다.
>
> 그렇지 않으면 실행되지 않습니다.
>
> 윈도우 환경에서는 `sudo certutil -addstore root mitmproxy-ca-cert.cer`로 인증합니다.
>
> Sudo가 활성화되어있지 않은 환경에서는 관리자로 상향된 쉘에서 실행합니다.
>
> MacOS 환경에서는 `sudo security add-trusted-cert -d -p ssl -p basic -k /Library/Keychains/System.keychain ~/.mitmproxy/mitmproxy-ca-cert.pem`으로 인증합니다.
>
> 다른 플렛폼은 수동으로 설정되어야만 합니다.
> https://docs.mitmproxy.org/stable/concepts/certificates/

현재 아래와 같은 환경에서 개발되며 테스트되고 있습니다.
- ✅ MacOS 26 Tahoe Developer Beta 2 (25A5295e) en-US aarch64
- ✅ Windows 11 Pro for Workstations 24H2 (26100.4351) en-US x86_64
- ✅ NixOS 25.05.804570.c7ab75210cb8 KDE 6 / Linux 6.15 x86_64

---
다음과 같은 명령어로 환경을 설정합니다.

설명하는 가이드를 잘 따라가면 설정할 수 있습니다.

```sh
uv run setup.py
```

uv 설치 후 다음과 같은 명령어를 입력합니다.

```sh
uv sync
```

venv와 패키지가 설치가 됩니다.

---

`uv run setup.py`로 환경을 설정합니다.

---

# 윈도우 인코딩 이슈 해결
이거 해결 방법
![image](https://github.com/user-attachments/assets/01ca45c2-fda9-44fb-83fc-39daa7e52092)

![image](https://github.com/user-attachments/assets/55c502f5-0bf7-44f8-bbb4-1dc1e0c8c3c3)

이것도 setup.py 사용하면 반자동으로 할 수 있습니다.

못찾겠으면 intl.cpl 열어주세요.

# 실행

domains.txt는 실행시 자동으로 다운로드 됩니다.

```sh
curl "https://f.imnya.ng/.whs/tp-domains/data/domains/latest.txt" -o domains.txt
```

```sh
# uv run run.py {domains.txt 시작 줄} {domains.txt 끝 줄} {--skh} {--no-download}
uv run run.py 1 100 --skh
```

# Prompt 확장 가이드

## 1. 파일 생성

`lib/llm/prompt` 폴더에서 fallback 폴더를 복사하여

원하는 프로바이더를 추가해줍니다. `ex) lib/llm/prompt/Google/`

## 2. prompt.py 수정

Prompt에서 추가한 파일을 prompt.py에서 수정합니다.

만약 로그인 정보를 넣고 싶다면 Sensitive
`Log into example.com as user x_username with password x_password`

## 3. model.py

응답할 때 원하는 리턴 값을 `dict`로 받습니다.

## 4. \_\_init\_\_.py 수정
![image](https://github.com/user-attachments/assets/3aed2243-92d5-4359-8515-6d2f9bfa100b)

추가한 prompt에 따라 import합니다.

## 5. 사용 방법
```py
from lib.llm.prompt.fallback import prompt, model
```

# 참고하면 좋을만한 것

- [ ] 일부 웹사이트는 사용자의 언어에 따라 OAuth 옵션을 바꾸기도 합니다.
- [ ] https://docs.browser-use.com/customize/custom-functions
