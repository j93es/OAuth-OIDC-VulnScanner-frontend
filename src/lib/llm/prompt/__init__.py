from typing import Union, Type
from pydantic import BaseModel

def get_prompt(type: str) -> tuple[str, Type[BaseModel]] | str:
    """
    Prompt를 반환합니다.

    :param type: 'auth' {Auth List} 또는 'google' {OAuth Provider}, 'meta' {OAuth Provider}을 지정합니다.
    :return: 해당하는 프롬프트 문자열 또는 (프롬프트, 모델) 튜플
    """
    if type.lower() == "auth":
        from lib.llm.prompt._get_oauth import prompt, model
        return prompt, model
    
    elif type.lower() in ["google", "google account"]:
        from lib.llm.prompt.google import prompt, model
        return prompt, model
    
    elif type.lower() in ["microsoft", "microsoftonline"]:
        from lib.llm.prompt.microsoft import prompt, model
        return prompt, model
    
    elif type.lower() in ["meta", "facebook"]:
        from lib.llm.prompt.facebook import prompt, model
        return prompt, model
    
    elif type.lower() in ["apple"]:
        from lib.llm.prompt.apple import prompt, model
        return prompt, model

    elif type.lower() in ["github"]:
        from lib.llm.prompt.github import prompt, model
        return prompt, model

    else:
        from lib.llm.prompt._fallback import model, prompt
        return prompt, model
