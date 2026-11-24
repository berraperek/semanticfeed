from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    APP_NAME: str = "SemanticFeed API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    DATABASE_URL: str = (
        "postgresql://semanticfeed:semanticfeed@localhost:5433/semanticfeed"
    )
    TEST_DATABASE_URL: str = (
        "postgresql://semanticfeed:semanticfeed@localhost:5433/semanticfeed_test"
    )


settings = Settings()
