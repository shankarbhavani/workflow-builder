"""
Application configuration using pydantic-settings
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # API Settings
    PROJECT_NAME: str = "Workflow Builder"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/workflow_builder"

    # Temporal
    TEMPORAL_HOST: str = "temporal:7233"
    TEMPORAL_NAMESPACE: str = "default"
    TEMPORAL_TASK_QUEUE: str = "workflow-builder-queue"

    # Action Service (AI Agent Actions API)
    ACTION_SERVICE_URL: str = "http://localhost:8081"
    ACTION_SERVICE_AUTH_USER: str = "digital-workforce@fourkites.com"
    ACTION_SERVICE_AUTH_PASSWORD: str = "F0urK it3sR0cks!@#"

    # External Action Service (for chat workflow generation)
    EXTERNAL_ACTION_SERVICE_URL: str = "https://service-dev.ng-np.fourkites.com"

    # JWT Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production-min-32-chars-long"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Azure OpenAI
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_DEPLOYMENT_NAME: str
    AZURE_OPENAI_API_VERSION: str = "2024-12-01-preview"

    # AWS S3 (for Gmail to S3 action)
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "fk-sam-files"

    # Test Mode Configuration
    TEST_S3_PRESIGNED_URL: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
