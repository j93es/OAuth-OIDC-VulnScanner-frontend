from typing import List
from pydantic import BaseModel

# 출력 모델
class OAuth(BaseModel):
    provider: str
    oauth_uri: str


class OAuthList(BaseModel):
    oauth_providers: List[OAuth]