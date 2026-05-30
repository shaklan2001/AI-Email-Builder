from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_name: str = "email-workflow-builder"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_url: str = "http://localhost:5173"
    cors_origins: str = "http://localhost:5173"
    clerk_pem_public_key: str = ""
    clerk_secret_key: str = ""
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    resend_api_key: str = ""
    resend_from_email: str = "onboarding@resend.dev"
    mongodb_user: str = "shaklan2001"
    mongodb_password: str = ""
    mongodb_host: str = "cluster0.exphul2.mongodb.net"
    mongodb_db_name: str = "email_workflow_builder"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def mongodb_connection_url(self) -> str:
        password = self.mongodb_password.strip()
        if not password:
            raise ValueError(
                "MONGODB_PASSWORD is required. Put the Atlas password in .env — "
                "do not embed it in a connection URL (special chars like @ break parsing)."
            )
        user = quote_plus(self.mongodb_user.strip())
        encoded_password = quote_plus(password)
        host = self.mongodb_host.strip().rstrip("/")
        return f"mongodb+srv://{user}:{encoded_password}@{host}/"


settings = Settings()
