import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "complite-study")
    app_env: str = os.getenv("APP_ENV", "dev")
    host: str = os.getenv("APP_HOST", "0.0.0.0")
    port: int = int(os.getenv("APP_PORT", "8000"))
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/complite_study.db")
    storage_dir: str = os.getenv("STORAGE_DIR", "./storage")
    storage_backend: str = os.getenv("STORAGE_BACKEND", "s3")

    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")

    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    bedrock_model_id: str = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")
    s3_bucket: str = os.getenv("S3_BUCKET", "")
    s3_region: str = os.getenv("S3_REGION", "")
    s3_prefix: str = os.getenv("S3_PREFIX", "complite-study/materials")


settings = Settings()
