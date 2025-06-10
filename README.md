# 참고하면 좋을만한 것

- [ ] 일부 웹사이트는 사용자의 언어에 따라 OAuth 옵션을 바꾸기도 합니다.
- [ ] https://docs.browser-use.com/customize/custom-functions

# 환경 설정

이 프로젝트는 [uv](https://docs.astral.sh/uv/getting-started/installation/)라는 Python 패키지 관리자를 사용하여 설정해야합니다.

또한 [oauth-backend](https://github.com/j93es/oauth-backend)가 설정되길 권장합니다.
> 프록시를 사용한다면 이 가이드에 따라 인증서 또한 설정되어야만 합니다.
>
> 그렇지 않으면 실행되지 않습니다.
>
> 윈도우 환경에서는 `sudo  certutil -addstore root mitmproxy-ca-cert.cer`로 인증합니다.
> 
> Sudo가 활성화되어있지 않은 환경에서는 관리자로 상향된 쉘에서 실행합니다.
>
> MacOS 환경에서는 `sudo security add-trusted-cert -d -p ssl -p basic -k /Library/Keychains/System.keychain ~/.mitmproxy/mitmproxy-ca-cert.pem`으로 인증합니다.
>
> 다른 플렛폼은 수동으로 설정되어야만 합니다.
> https://docs.mitmproxy.org/stable/concepts/certificates/

---

uv 설치 후 다음과 같은 명령어를 입력합니다.

```sh
uv sync
```

venv와 패키지가 설치가 됩니다.

browser_use가 Playwright에 대한 의존성이 있어 브라우저 설치가 필요합니다

```sh
uv run playwright install
```

다음과 같은 명령어로 실행합니다.

```sh
uv run main.py
```

Environment는 .env.example에 따라 설정되어야합니다.

.env.example을 .env로 복사하여서 사용해주세요.

# 실행

```sh
# domains.txt 받기
curl "https://f.imnya.ng/.whs/tp-domains/data/domains/latest.txt" -o domains.txt

# ./run.sh {domains.txt 시작 줄} {domains.txt 끝 줄} {HTML 검사 Skip}
./run.sh 12540 13000 False
```


```pwsh
# domains.txt 받기
curl "https://f.imnya.ng/.whs/tp-domains/data/domains/latest.txt" -o domains.txt
# ./run.ps1 {domains.txt 시작 줄} {domains.txt 끝 줄} {HTML 검사 Skip}
./run.ps1 12540 13000 False
```
