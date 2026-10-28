from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from cryptography.fernet import Fernet


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./taxsphere-local.db"
    jwt_secret: str = "development-only-change-me"
    jwt_issuer: str = "taxsphere-india"
    app_environment: str = "development"
    secure_cookies: bool = False
    documents_encryption_key: str | None = None
    frontend_origin: str = "http://localhost:3000"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def require_production_settings(self):
        if self.app_environment.lower() == "production":
            # Render supplies PostgreSQL connection strings without a driver
            # suffix and exposes its service hostnames without a URL scheme.
            if self.database_url.startswith("postgres://"):
                self.database_url = "postgresql+asyncpg://" + self.database_url[len("postgres://"):]
            elif self.database_url.startswith("postgresql://"):
                self.database_url = "postgresql+asyncpg://" + self.database_url[len("postgresql://"):]
            if self.database_url.startswith("postgresql+asyncpg://"):
                url, separator, query = self.database_url.partition("?")
                if "sslmode=require" in query:
                    query = query.replace("sslmode=require", "ssl=require")
                elif "ssl=require" not in query:
                    query += ("&" if query else "") + "ssl=require"
                self.database_url = url + "?" + query
            if self.frontend_origin and not self.frontend_origin.startswith(("http://", "https://")):
                self.frontend_origin = "https://" + self.frontend_origin
            if not self.database_url.startswith("postgresql+asyncpg://"):
                raise ValueError("Production requires PostgreSQL DATABASE_URL")
            if len(self.jwt_secret) < 32 or self.jwt_secret == "development-only-change-me":
                raise ValueError("Production requires a random JWT_SECRET of at least 32 characters")
            if not self.documents_encryption_key:
                raise ValueError("Production requires DOCUMENTS_ENCRYPTION_KEY")
            if "development-only" in self.jwt_secret.lower() or "replace-with" in self.jwt_secret.lower():
                raise ValueError("Production JWT_SECRET must not be a placeholder")
            if "ssl=require" not in self.database_url and "sslmode=require" not in self.database_url:
                raise ValueError("Production DATABASE_URL must require TLS")
            if not self.frontend_origin.startswith("https://"):
                raise ValueError("Production FRONTEND_ORIGIN must use HTTPS")
            try:
                Fernet(self.documents_encryption_key.encode("ascii"))
            except (ValueError, UnicodeEncodeError) as error:
                raise ValueError("DOCUMENTS_ENCRYPTION_KEY must be a valid Fernet key") from error
        return self


settings = Settings()
