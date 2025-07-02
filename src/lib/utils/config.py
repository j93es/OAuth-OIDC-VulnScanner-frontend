import os

from dotenv import load_dotenv

load_dotenv(verbose=True, override=True)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:11081")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")
GOOGLE_PLANNER_MODEL = os.getenv("GOOGLE_PLANNER_MODEL")
