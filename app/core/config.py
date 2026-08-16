import os
import secrets
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator

class Settings(BaseSettings):
    APP_NAME: str = "Portalitics"
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "portalitics_secret_key_2026"
    APP_PORT: int = 8000

    DEMO_MODE: bool = False

    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "portalitics_db"

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    AT_RISK_ATTENDANCE_THRESHOLD: float = 75.0
    AT_RISK_GRADE_DROP_PERCENT: float = 15.0
    RISK_WEIGHT_ATTENDANCE: float = 0.3
    RISK_WEIGHT_GRADES: float = 0.3
    RISK_WEIGHT_ASSIGNMENTS: float = 0.2
    RISK_WEIGHT_SUBMISSION_DELAYS: float = 0.2

    AT_RISK_SUPPORT_THRESHOLD: float = 30.0
    AT_RISK_IMMEDIATE_THRESHOLD: float = 55.0

    INTERVENTION_EVALUATION_WINDOW_DAYS: int = 14

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def validate_secret_key(self) -> 'Settings':
        invalid_placeholders = {
            "",
            "portalitics_secret_key_2026",
            "portalitics_secret_key_change_in_production_2026",
            "<REPLACE_WITH_A_STRONG_RANDOM_HEX_KEY>",
        }

        # Production must fail closed if the secret is weak or missing.
        if self.APP_ENV == "production":
            if not self.APP_SECRET_KEY or self.APP_SECRET_KEY.strip() in invalid_placeholders:
                raise ValueError(
                    "Security Risk: APP_SECRET_KEY is missing or set to a default placeholder! "
                    "You must configure a strong key in your environment or .env file."
                )
            return self

        # Development and testing should still boot even if the local .env is stale.
        if not self.APP_SECRET_KEY or self.APP_SECRET_KEY.strip() in invalid_placeholders:
            self.APP_SECRET_KEY = secrets.token_hex(32)
        return self

settings = Settings()
