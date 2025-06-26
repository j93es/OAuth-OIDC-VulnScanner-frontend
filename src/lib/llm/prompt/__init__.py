# why this is isn't index
# 이 파일을 __init__.py로 만든 이유는
# 굳이 이 짧은 코드를 파일을 하나 더 만드는게 코드의 가독성을 떨어뜨린다고 판단했기 때문입니다.

def get_prompt(type:str) -> str:
    """
    Prompt를 반환합니다.

    :param type: 'auth' {Auth List} 또는 'google' {OAuth Provider}, 'meta' {OAuth Provider}을 지정합니다.
    :return: 해당하는 프롬프트 문자열
    """
    if type.lower() == "auth":
        from lib.llm.prompt.auth_list import extract_oauth_list_prompt
        return extract_oauth_list_prompt

    else:
        from lib.llm.prompt.fallback import extend_planner_system_message
        return extend_planner_system_message
