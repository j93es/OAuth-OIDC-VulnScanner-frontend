from dotenv import load_dotenv
import os

from lib.llm.prompt import llm_login, session

load_dotenv(override=True)

def extend_planner_system_message():
  if os.getenv("PROVIDOR_CREDENTIALS_IN_LLM", "False").lower() == "true":
    return llm_login.extend_planner_system_message
  else:
    return session.extend_planner_system_message