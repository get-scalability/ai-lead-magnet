from pydantic import PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ANTHROPIC_API_KEY: SecretStr

    DATABASE_URL: PostgresDsn

    GOTENBERG_URL: str = "http://gotenberg:3000"

    PINECONE_RW_API_KEY: SecretStr | None = None

    SCALA_APP_API_KEY: SecretStr
    SCALA_APP_API_URL: str = "https://api.getscalability.io/"
    SCALA_TENANT_ID: str = "scalability"
    SCALA_CRM_API_URL: str = "https://crm.getscalability.io/"


settings = Settings()  # type: ignore[call-arg]
