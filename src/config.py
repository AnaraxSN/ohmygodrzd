from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Telegram Bot
    telegram_bot_token: str
    telegram_webhook_url: Optional[str] = None
    
    # Database
    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    
    # RZD Settings
    rzd_base_url: str = "https://pass.rzd.ru"
    scraping_delay: int = 5
    max_concurrent_requests: int = 3
    
    # Monitoring
    check_interval_minutes: int = 10
    max_subscriptions_per_user: int = 5
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/bot.log"
    
    class Config:
        env_file = ".env"


settings = Settings()

