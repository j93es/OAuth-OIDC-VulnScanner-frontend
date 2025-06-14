from dotenv import load_dotenv
import os

load_dotenv(override=True)

def extend_planner_system_message():
  if os.getenv("PROVIDOR_CREDENTIALS_IN_LLM", "False").lower() == "true":
    from lib.prompt import llm_login
    return llm_login.extend_planner_system_message
  else:
    from lib.prompt import session
    return session.extend_planner_system_message