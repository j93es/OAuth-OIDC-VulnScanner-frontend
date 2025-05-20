# 참고하면 좋을만한 것
- [ ] 일부 웹사이트는 사용자의 언어에 따라 OAuth 옵션을 바꾸기도 합니다.
- [ ] https://docs.browser-use.com/customize/custom-functions

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

Environment에는 다음과 같은 값이 들어갑니다.
```
ANONYMIZED_TELEMETRY=false

OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://models.github.ai/inference # 선택
OPENAI_MODEL=openai/gpt-4o-mini # Github Models가 아닐시 gpt-4.1

# 선택
PROXY_HOST=127.0.0.1
PROXY_PORT=8080
```

`OPENAI_BASE_URL`은 GitHub Models가 아닐시 비워둡니다.

`OPENAI_MODEL`은 GitHub Models가 아닐시 `openai/`를 제거합니다.

`PROXY_HOST`와 `PROXY_PORT`는 만약 Caido를 사용 중일 시 환경에 맞게 설정 후 설정합니다.
