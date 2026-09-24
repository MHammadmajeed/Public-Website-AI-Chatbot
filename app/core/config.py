from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    app_url: str = "http://localhost:8000"
    allowed_origins: str = "http://localhost:3000"
    app_secret: str = "change-me"

    database_url: str

    llm_provider: str = "anthropic"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None

    embedding_model: str = "gemini-embedding-001"

    email_provider: str = "smtp"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    resend_api_key: str | None = None
    lead_email_to: str = "info@moinsystemsai.com"
    # Free-tier Resend accounts can only send to the address the account
    # was signed up with. During local development, emails are sent here
    # instead of lead_email_to; in production (app_env != "local") this
    # is ignored and lead_email_to is used directly (task 6.3).
    lead_email_dev_to: str | None = None

    rate_limit: str = "60/minute"
    retrieval_top_k: int = 5
    retrieval_threshold: float = 0.55

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def effective_lead_email_to(self) -> str:
        """The address emails actually get sent to right now."""
        if self.app_env == "local" and self.lead_email_dev_to:
            return self.lead_email_dev_to
        return self.lead_email_to


@lru_cache
def get_settings() -> Settings:
    return Settings()