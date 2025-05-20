import asyncio
import json
from typing import List
from dotenv import load_dotenv
from browser_use import Agent, Browser, BrowserConfig, Controller
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from lib.browser_config import browser_config_kwargs
import os
import csv

load_dotenv()

if os.getenv("OPENAI_API_KEY") is None:
    raise ValueError("OPENAI_API_KEY environment variable not set.")
if os.getenv("OPENAI_MODEL") is None:
    raise ValueError("OPENAI_MODEL environment variable not set.")

browser_config_kwargs = browser_config_kwargs()

browser = Browser(
    config=BrowserConfig(**browser_config_kwargs)
)

class OAuth(BaseModel):
    source: str
    provider: str
    client_id: str
    redirect_uri: str
    response_type: str
    scope: str
    oauth_uri: str

class OAuthExists(BaseModel):
    oauth_providers: List[str]

controller = Controller(output_model=OAuthExists)

extend_planner_system_message = """
{"oauth_providers": ["GitHub", "Google", "Facebook", "Twitter", "LinkedIn", "GitLab", "Bitbucket", "Discord", "Reddit", "Spotify", "Twitch", "Yahoo", "Amazon", "Microsoft", "Apple", ...]}

The OAuth providers are available on the login page of the website.
The user is interested in the OAuth providers available on the login page of the website.

Passkey isn't a Oauth provider. Remove it from the list of OAuth providers.
"""

async def main():
    url = "https://auth0.com"
    agent = Agent(
        browser=browser,
        task=f"Go to {url}, navigate to the login page, and identify the available OAuth providers. Passkey is not a valid OAuth provider.",
        llm=ChatOpenAI(
            model=os.getenv("OPENAI_MODEL"), 
            temperature=0.0
        ),
        controller=controller,
        extend_planner_system_message=extend_planner_system_message,
    )

    response = await agent.run()
    final_result = response.final_result()
    if final_result is None:
        raise ValueError("final_result() returned None")
    result = json.loads(final_result)
    print(result)
    
    # {"oauth_providers": ["GitHub", "Passkey"]} print
    # Clear Terminal
    print("\033c", end="")
    print(f"🔗: {url}")
    for provider in result['oauth_providers']:
        print(provider)


asyncio.run(main())
