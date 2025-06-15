from langchain.callbacks.base import BaseCallbackHandler
from langchain_google_genai import ChatGoogleGenerativeAI

class QuotaExhaustedHandler(BaseCallbackHandler):
    def on_llm_error(self, error, **kwargs):
        if "ResourceExhausted" in str(error) or "429" in str(error):
            print("⚠️ API 쿼터가 소진되었습니다. 재시도 로직에 위임합니다...")
            # backoff handled in scan_one_url

def CreateChatGoogleGenerativeAI(model: str):
    """재시도 로직이 포함된 LLM 생성"""
    if model == "fallback":
        print("⚠️ Fallback 모델을 사용합니다. Envorinment 변수를 확인하세요.")
        print("⚠️ Model Gemini-2.0-flash-lite를 사용합니다.")
        model = "gemini-2.0-flash-lite"
    return ChatGoogleGenerativeAI(
        model=model,
        max_retries=10,  # 최대 재시도 횟수 증가
        model_kwargs={
            "request_timeout": 120,  # 타임아웃 시간 증가 (2분)
        },
        callbacks=[QuotaExhaustedHandler()],
        # API 호출 간격 조정
        temperature=0.1,
    )
