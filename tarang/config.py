import os
import json
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv("/etc/secrets/tarang.env")
load_dotenv(override=True)


def whatsapp_routes_from_env():
    try:
        routes = json.loads(os.getenv("WHATSAPP_ROUTES", "{}"))
        if isinstance(routes, dict) and all(
            isinstance(k, str)
            and k.isdigit()
            and isinstance(v, str)
            and 0 < len(v) <= 100
            for k, v in routes.items()
        ):
            return routes
    except ValueError:
        pass
    return {}  # Invalid routing disables intake without taking Telegram offline.


@dataclass
class Settings:
    speech_key: str = field(default_factory=lambda: os.getenv("GNANI_API_KEY", ""))
    speech_voice: str = field(
        default_factory=lambda: os.getenv("GNANI_VOICE", "Kaveri")
    )
    public_demo: bool = field(
        default_factory=lambda: os.getenv("PUBLIC_DEMO_ENABLED", "false") == "true"
    )
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
        default_factory=lambda: os.getenv(
            "MODEL", "nvidia/nemotron-3-super-120b-a12b:free"
        )
    )
    timezone: str = field(default_factory=lambda: os.getenv("TIMEZONE", "Asia/Kolkata"))
    free_host: bool = field(default_factory=lambda: os.getenv("RENDER") == "true")
    telegram_mode: str = field(
        default_factory=lambda: os.getenv("TELEGRAM_MODE", "polling")
    )

    whatsapp_enabled: bool = field(
        default_factory=lambda: os.getenv("WHATSAPP_ENABLED") == "true"
    )
    whatsapp_app_secret: str = field(
        default_factory=lambda: os.getenv("WHATSAPP_APP_SECRET", "")
    )
    whatsapp_verify_token: str = field(
        default_factory=lambda: os.getenv("WHATSAPP_VERIFY_TOKEN", "")
    )
    whatsapp_phone_id: str = field(
        default_factory=lambda: os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    )
    # Explicit sender -> wedding scope routing, never infer a shared wedding.
    whatsapp_routes: dict[str, str] = field(default_factory=whatsapp_routes_from_env)
    group_enabled: bool = field(
        default_factory=lambda: os.getenv("WHATSAPP_GROUP_ENABLED") == "true"
    )
    group_id: str = field(default_factory=lambda: os.getenv("WHATSAPP_GROUP_ID", ""))
    group_bridge_token: str = field(
        default_factory=lambda: os.getenv("WHATSAPP_BRIDGE_TOKEN", "")
    )
