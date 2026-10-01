import json
from pathlib import Path
import httpx
from .schema import Decision


class OpenRouter:
    def __init__(self, settings):
        self.settings = settings

    async def decide(self, context):
        if not self.settings.model_key:
            raise RuntimeError("model_not_configured")
        root = Path(__file__).resolve().parent.parent
        persona = (
            (root / "prompts/tarang-persona.md")
            .read_text()
            .split("## Full prompt / agent-ready version")[1]
            .split("## Short version")[0]
        )
        policy = (root / "prompts/runtime.md").read_text()
        return await self.structured(context, policy + "\n" + persona, Decision)

    async def detect_conflicts(self, context):
        from .schema import ConflictReport

        policy = (
            Path(__file__).resolve().parent.parent / "prompts/conflicts.md"
        ).read_text()
        return await self.structured(context, policy, ConflictReport)

    async def structured(self, context, policy, schema):
        if not self.settings.model_key:
            raise RuntimeError("model_not_configured")
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": "Bearer " + self.settings.model_key},
                json={
                    "model": self.settings.model,
                    "messages": [
                        {"role": "system", "content": policy},
                        {"role": "user", "content": json.dumps(context)},
                    ],
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "tarang_decision",
                            "strict": True,
                            "schema": schema.model_json_schema(),
                        },
                    },
                    "provider": {"require_parameters": True},
                    "max_tokens": 4000,
                    "temperature": 0.3,
                },
            )
            if response.status_code != 200:
                raise RuntimeError(f"model_http_{response.status_code}")
            return schema.model_validate_json(
                response.json()["choices"][0]["message"]["content"]
            )


class Telegram:
    def __init__(self, token):
        self.token = token

    async def call(self, method, payload):
        if not self.token:
            raise RuntimeError("telegram_not_configured")
        async with httpx.AsyncClient(timeout=40) as client:
            response = await client.post(
                f"https://api.telegram.org/bot{self.token}/{method}", json=payload
            )
            # Never include raw URLs or exception bodies containing bot token in logs.
            if response.status_code != 200 or not response.json().get("ok"):
                raise RuntimeError(f"telegram_http_{response.status_code}")
            return response.json()["result"]
