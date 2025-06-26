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
        with requests.get(url, timeout=timeout, stream=True) as response:
            # 응답 코드가 200번대가 아니면 False로 간주
            if not response.ok:
                return False

            content_type = response.headers.get('Content-Type', '')
            # Content-Type에 'text/html'이 포함되어 있으면 HTML로 간주
            return content_type.lower().startswith('text/html')
    except requests.RequestException:
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
