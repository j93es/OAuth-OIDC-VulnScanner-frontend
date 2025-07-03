from typing import List

from pydantic import BaseModel


# 출력 모델
class OAuth(BaseModel):
    provider: str
    oauth_uri: str = ""  # OAuth 리스트 추출 단계에서는 URI가 없을 수 있음


class OAuthList(BaseModel):
    oauth_providers: List[str]  # 이제 문자열 배열로 변경


# 기존 모델 유지 (backward compatibility)
BaseModel = OAuthList
