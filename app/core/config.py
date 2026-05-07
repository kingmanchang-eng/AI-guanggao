from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_ENV: str = "production"
    APP_BASE_URL: str = ""
    FRONTEND_BASE_URL: str = ""
    API_KEY: str = ""

    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_ANON_KEY: str = ""

    GOOGLE_ADS_DEVELOPER_TOKEN: str = ""
    GOOGLE_ADS_CLIENT_ID: str = ""
    GOOGLE_ADS_CLIENT_SECRET: str = ""
    GOOGLE_ADS_USE_PROTO_PLUS: bool = True

    AI_PROVIDER: str = "openai"
    AI_API_KEY: str = ""
    AI_MODEL: str = "gpt-4o"
    AI_REQUEST_TIMEOUT_SECONDS: int = 120

    GLOBAL_DAILY_MUTATE_LIMIT: int = 500
    DEFAULT_SITE_DAILY_ACTION_LIMIT: int = 50
    DEFAULT_BUDGET_CHANGE_RATE_CAP: float = 0.15
    ENABLE_VALIDATE_ONLY: bool = True
    ENABLE_PRODUCTION_MUTATE: bool = False

    ENABLE_SCHEDULER: bool = True
    TIMEZONE: str = "Asia/Shanghai"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
