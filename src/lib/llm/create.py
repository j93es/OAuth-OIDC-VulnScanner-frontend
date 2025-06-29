from browser_use.llm import ChatGoogle
from dotenv import load_dotenv

# 환경 변수 로드 (GOOGLE_API_KEY 필요)
load_dotenv(override=True)

def CreateChatGoogle(model: str):
    """Browser Use용 Google 모델 생성"""
    if model == "fallback":
        print("⚠️ Fallback 모델을 사용합니다. Environment 변수를 확인하세요.")
        print("⚠️ Model gemini-2.0-flash-lite를 사용합니다.")
        model = "gemini-2.0-flash-lite"
    
    return ChatGoogle(
        model=model,
        temperature=0.0,
        # Browser Use는 내부적으로 재시도 로직을 처리합니다
    )