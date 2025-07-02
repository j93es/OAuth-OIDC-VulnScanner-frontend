from pydantic import BaseModel

class model(BaseModel):
    msg: str | None = None
    url: str | None = None
    sso_list: list[str] = []  # List of SSO providers found on the login page
