import os
from dotenv import load_dotenv

load_dotenv(override=True)

def get_prompt(type:str) -> str:
    """
    Prompt를 반환합니다.
    
    :param type: 'extend_planner' 또는 'oauth_login'
    :return: 해당하는 프롬프트 문자열
    """
    if type == "auth":
        from lib.llm.prompt.auth_list import extract_oauth_list_prompt
        return extract_oauth_list_prompt
    else:
        from lib.llm.prompt.fallback import extend_planner_system_message
        return extend_planner_system_message