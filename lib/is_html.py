import requests

def is_html_url(url: str, timeout: float = 10.0) -> bool:
    """
    주어진 URL에 HEAD 요청을 보내고, 응답 헤더의 Content-Type이 HTML인지 확인합니다.
    - url: 검사할 URL 문자열
    - timeout: 요청 타임아웃(초 단위)
    
    반환값:
    - Content-Type이 'text/html' 로 시작하면 True, 그렇지 않으면 False
    """

    try:
        # HEAD 요청으로 헤더만 가져와도 충분하지만, 일부 서버에서 HEAD를 허용하지 않을 수 있어
        # GET 요청을 사용해도 무방합니다. 단, GET은 바디를 가져오기 때문에 HEAD보다 비용이 높을 수 있음.
        response = requests.head(url, timeout=timeout, allow_redirects=True)

        # 만약 HEAD 요청에 실패하거나 서버가 405(Method Not Allowed)를 반환하면, GET 요청으로 재시도
        if response.status_code == 405:
            response = requests.get(url, timeout=timeout, stream=True)

        # 응답 코드가 200번대가 아니면 False로 간주
        if not response.ok:
            return False

        content_type = response.headers.get('Content-Type', '')
        # Content-Type에 'text/html'이 포함되어 있으면 HTML로 간주
        return content_type.lower().startswith('text/html')

    except requests.RequestException as e:
        # 네트워크 오류, 타임아웃 등 예외 발생 시 False 반환
        # 필요하다면 로그를 찍거나 예외를 다시 던질 수 있습니다.
        print(f"Error fetching URL: {e}")
        return False

if __name__ == '__main__':
    test_urls = [
        'https://www.example.com',
        'https://api.github.com',        # JSON API라서 HTML이 아닐 확률이 높음
        'https://raw.githubusercontent.com'  # 텍스트 파일 등 다양한 타입
    ]

    for url in test_urls:
        if is_html_url(url):
            print(f"[HTML] {url}")
        else:
            print(f"[Not HTML] {url}")
