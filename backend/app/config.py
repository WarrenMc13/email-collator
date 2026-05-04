from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://propflow:propflow@localhost:5432/propflow"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    # Mailbox password encryption key (32 url-safe base64 chars)
    encryption_key: str = "placeholder-replace-with-fernet-key"

    # SendGrid
    sendgrid_api_key: str = ""
    from_email: str = "noreply@propflow.co.za"

    # WhatsApp Business
    whatsapp_token: str = ""
    whatsapp_phone_id: str = ""

    # BulkSMS
    bulksms_username: str = ""
    bulksms_password: str = ""

    # DocuSign
    docusign_integration_key: str = ""
    docusign_account_id: str = ""

    # S3 / MinIO
    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "propflow"

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""


settings = Settings()
