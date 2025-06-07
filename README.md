# 참고하면 좋을만한 것

- [ ] 일부 웹사이트는 사용자의 언어에 따라 OAuth 옵션을 바꾸기도 합니다.
- [ ] https://docs.browser-use.com/customize/custom-functions

https://f.imnya.ng/.whs/tp-domains/data/domains/latest.txt
이거 도메인 리스트 HTML만 필터링 해둔거니까 이거 쓰면 좋을 것 같습니다.

# 환경 설정

이 프로젝트는 [uv](https://docs.astral.sh/uv/getting-started/installation/)라는 Python 패키지 관리자를 사용하여 설정해야합니다.

uv 설치 후 다음과 같은 명령어를 입력합니다.

```
uv sync
```

venv와 패키지가 설치가 됩니다.

browser_use가 Playwright에 대한 의존성이 있어 브라우저 설치가 필요합니다

```
playwright install chromium --with-deps --no-shell
```

다음과 같은 명령어로 실행합니다.

```
uv run main.py
```

Environment는 .env.example에 따라 설정되어야합니다.

.env.example을 .env로 복사하여서 사용해주세요.

# 실행

```sh
# ./run.sh {domains.txt 시작 줄} {domains.txt 끝 줄} {HTML 검사 Skip}
./run.sh 12540 13000 False
```


```pwsh
# ./run.ps1 {domains.txt 시작 줄} {domains.txt 끝 줄} {HTML 검사 Skip}
./run.ps1 12540 13000 False
```