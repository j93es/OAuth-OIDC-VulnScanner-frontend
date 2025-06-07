import asyncio
import json
import os
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Agent, Browser, BrowserConfig, Controller
from browser_use.browser.context import BrowserContext, BrowserContextConfig
from lib.browser_config import browser_config_kwargs
import csv

load_dotenv()

# Check environment variables
if os.getenv("GOOGLE_API_KEY") is None:
    raise ValueError("OPENAI_API_KEY environment variable not set.")
if os.getenv("GOOGLE_MODEL") is None:
    raise ValueError("OPENAI_MODEL environment variable not set.")
if os.getenv("GOOGLE_PLANNER_MODEL") is None:
    raise ValueError("OPENAI_PLANNER_MODEL environment variable not set.")

# Configure browser
browser = Browser(
    config=BrowserConfig(**browser_config_kwargs())
)

# Set browser context
context = BrowserContext(
    browser=browser,
    config=BrowserContextConfig(
        wait_for_network_idle_page_load_time=3.0,
        window_width=1600,
        window_height=900,
        locale='en-US',
        highlight_elements=True,
        viewport_expansion=500,
        keep_alive=True
    )
)

# Output model: each result is one OAuth entry with metadata
class OAuth(BaseModel):
    provider: str
    oauth_uri: str

class OAuthList(BaseModel):
    oauth_providers: List[OAuth]

controller = Controller(output_model=OAuthList)

# Extended planner prompt
extend_planner_system_message = """
🎯 Your mission is to collect the real OAuth login URLs from the website.

1. First, go to the website’s **login page**.
2. On the login page, look for OAuth login buttons. These usually say things like **"Continue with Google"**, **"Sign in with GitHub"**, etc.
3. ⚠️ **DO NOT collect or include "Passkey"** — it is NOT an OAuth provider.

---

✅ For EACH OAuth button you find:

- **Try opening it in a new tab**. If it redirects to an OAuth URL (e.g. `https://accounts.google.com/...`, `https://github.com/login/oauth/...`), copy that **exact final URL**.
- If it **doesn’t open in a new tab**, **click the button** and wait for the redirect to happen.
  - As soon as you see the redirected URL with **client_id**, **redirect_uri**, etc., copy that **entire URL without changing or hiding anything**.
  - Then come back to the original tab (if needed) and continue with the next provider.

---

💡 **Do not guess** the OAuth URLs — only collect them by actually interacting with the buttons.

🚫 **Do not redact or mask any part** of the URL, including `client_id`, `redirect_uri`, `state`, or any other parameters. Record them exactly as they appear.

✅ Return a list of all OAuth providers and their **full raw redirect URLs** in this exact format:

```json
[
  {
    "provider": "Google",
    "oauth_uri": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...&redirect_uri=...&...",
  },
  {
    "provider": "GitHub",
    "oauth_uri": "https://github.com/login/oauth/authorize?client_id=...&redirect_uri=...",
  }
]
```
"""

# Main async runner
async def main():
    url = "https://git.imnya.ng"

    agent = Agent(
        browser_context=context,
        browser=browser,
        task=f"Go to {url}, navigate to the login page, and collect the OAuth provider buttons and their login URLs. Ignore Passkey.",
        llm=ChatGoogleGenerativeAI(model=os.getenv("GOOGLE_MODEL")),
        planner_llm=ChatGoogleGenerativeAI(model=os.getenv("GOOGLE_PLANNER_MODEL")),
        controller=controller,
        extend_planner_system_message=extend_planner_system_message,
    )

    # Run the agent
    response = await agent.run()
    final_result = response.final_result()
    if final_result is None:
        raise ValueError("final_result() returned None")

    data = json.loads(final_result)

    try:
        oauth_entries: List[OAuth] = [OAuth(**entry) for entry in data["oauth_providers"]]
    except Exception as e:
        raise ValueError(f"Failed to parse result: {e}\nRaw result: {final_result}")


    # Clear terminal
    #print("\033c", end="")
    print("-" * 20)

    print(f"Raw result: {final_result}")

    print(f"🔗 Scanned URL: {url}\n")
    print("🔐 Detected OAuth Providers and URLs:")
    for entry in oauth_entries:
        if "<" in entry.oauth_uri or "..." in entry.oauth_uri:
            print(f"⚠️ WARNING: {entry.provider} URL may be masked or incomplete:\n{entry.oauth_uri}\n")
        else:
            print(f"- {entry.provider}: {entry.oauth_uri}")

    # Save the result to CSV (append mode, so you can continue later)
    # 이거 좀 이상한데 나중에 고쳐야 할듯 파일이 수정이 안됨
    csv_file = "oauth_providers.csv"
    file_exists = os.path.isfile(csv_file)
    with open(csv_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["issuer", "provider", "oauth_uri"])
        for entry in oauth_entries:
            writer.writerow([url, entry.provider, entry.oauth_uri])
    print(f"\n✅ OAuth providers saved to {csv_file}")

    # Save the result to JSON
    with open(f"oauth_providers_{url}.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"✅ OAuth providers saved to oauth_providers_{url}.json")


# Run it
asyncio.run(main())
