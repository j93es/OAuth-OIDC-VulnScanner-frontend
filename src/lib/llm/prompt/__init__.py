from typing import Union, Type
from pydantic import BaseModel

def get_prompt(type: str) -> tuple[str, Type[BaseModel]] | str:
    """
    Prompt를 반환합니다.

    :param type: 'auth' {Auth List} 또는 'google' {OAuth Provider}, 'meta' {OAuth Provider}을 지정합니다.
    :return: 해당하는 프롬프트 문자열 또는 (프롬프트, 모델) 튜플
    """
    if type.lower() == "auth":
        from lib.llm.prompt.get_oauth import prompt, model
        return prompt, model
    
    else:
        from lib.llm.prompt.fallback import model, prompt
        return prompt, model
