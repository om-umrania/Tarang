import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv("/etc/secrets/tarang.env")
load_dotenv(override=True)


@dataclass
class Settings:
    database: str = field(
        default_factory=lambda: os.getenv("DATABASE_URL")
        or os.getenv("DATABASE_PATH", ".runtime/tarang.sqlite3")
    )
    bot_token: str = field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    allowed: frozenset[int] = field(
        default_factory=lambda: frozenset(
            int(x)
            for x in os.getenv("TELEGRAM_ALLOWED_USER_IDS", "").split(",")
            if x.strip()
        )
    )
    webhook_secret: str = field(
        default_factory=lambda: os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
    )
    operator_token: str = field(default_factory=lambda: os.getenv("OPERATOR_TOKEN", ""))
    model_key: str = field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY", ""))
    model: str = field(
        default_factory=lambda: os.getenv("MODEL", "google/gemini-3.8-flash")
    )
    telegram_mode: str = field(
        default_factory=lambda: os.getenv("TELEGRAM_MODE", "polling")
    )
