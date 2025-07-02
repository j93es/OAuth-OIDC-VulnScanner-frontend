from pydantic import BaseModel


class model(BaseModel):
    msg: str | None = None
    status: str | None = (
        None  # "success", "mfa_required", "google_blocked", "sso_not_found", "login_page_not_found", "invalid_credentials"
    )
    final_url: str | None = None
