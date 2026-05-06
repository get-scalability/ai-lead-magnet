from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from pydantic import PostgresDsn, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ANTHROPIC_API_KEY: SecretStr

    DATABASE_URL: PostgresDsn

    GOTENBERG_URL: str = "http://gotenberg:3000"

    PINECONE_RO_API_KEY: SecretStr

    SNOWFLAKE_ACCOUNT: str
    SNOWFLAKE_USER: str
    SNOWFLAKE_PRIVATE_KEY: SecretStr
    SNOWFLAKE_ROLE: str
    SNOWFLAKE_WAREHOUSE: str

    SCALA_APP_API_KEY: SecretStr
    SCALA_CRM_API_URL: str = "https://crm.getscalability.io/"

    @computed_field
    @property
    def SNOWFLAKE_SERIALIZED_KEY(self) -> bytes:  # noqa: N802
        private_key = serialization.load_pem_private_key(
            self.SNOWFLAKE_PRIVATE_KEY.get_secret_value().encode(),
            password=None,
            backend=default_backend(),
        )
        return private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )


settings = Settings()  # type: ignore[call-arg]
