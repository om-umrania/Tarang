"""Interactive local setup. Secrets never appear in shell arguments or output."""

import asyncio
import getpass
import os
from pathlib import Path
from dotenv import dotenv_values, set_key
from .adapters import Telegram, OpenRouter
from .config import Settings


async def main():
    path = Path(".env")
    path.touch(mode=0o600, exist_ok=True)
    path.chmod(0o600)
    values = dotenv_values(path)
    bot = values.get("TELEGRAM_BOT_TOKEN") or getpass.getpass(
        "BotFather token (hidden): "
    )
    try:
        telegram = Telegram(bot)
        me = await telegram.call("getMe", {})
    except Exception:
        raise SystemExit("Telegram credential check failed. No credential was printed.")
    set_key(path, "TELEGRAM_BOT_TOKEN", bot)
    print("Connected bot: @" + me["username"])
    key = values.get("OPENROUTER_API_KEY") or getpass.getpass(
        "OpenRouter API key (hidden): "
    )
    settings = Settings(model_key=key)
    try:
        await OpenRouter(settings).decide(
            {
                "incoming": {
                    "source": "synthetic-setup-check",
                    "text": "Introduce yourself briefly.",
                },
                "operations": [],
                "evidence": [],
                "budgets": [],
            }
        )
    except Exception:
        raise SystemExit(
            "OpenRouter credential/model check failed. Token is saved; model key has not been saved."
        )
    set_key(path, "OPENROUTER_API_KEY", key)
    print("OpenRouter connection verified.")
    print("Open your bot in Telegram and send /start. Then return here.")
    input("Press Enter after sending /start: ")
    updates = await telegram.call("getUpdates", {"timeout": 0})
    candidates = {
        u["message"]["from"]["id"]: u["message"]["from"].get("first_name", "")
        for u in updates
        if u.get("message", {}).get("chat", {}).get("type") == "private"
    }
    print("Private-chat candidates:", candidates)
    user = int(input("Your Telegram user ID from the list above: "))
    if user not in candidates:
        raise SystemExit("No matching private-chat update found. Nothing allowlisted.")
    set_key(path, "TELEGRAM_ALLOWED_USER_IDS", str(user))
    print(
        "Setup saved to ignored .env. Start with: python3 -m uvicorn tarang.app:app --host 127.0.0.1 --port 8766"
    )


if __name__ == "__main__":
    asyncio.run(main())
