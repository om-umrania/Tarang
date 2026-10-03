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

    async def demo_reply(self, context):
        from .public_demo import DemoReply

        policy = (
            Path(__file__).resolve().parent.parent / "prompts/public-demo.md"
        ).read_text()
        return await self.structured(context, policy, DemoReply, max_tokens=1600)

    async def intake_reply(self, context):
        from .intake import IntakeReply

        policy = (
            Path(__file__).resolve().parent.parent / "prompts/intake.md"
        ).read_text()
        return await self.structured(context, policy, IntakeReply, max_tokens=1800)

    async def detect_conflicts(self, context):
        from .schema import ConflictReport

        policy = (
            Path(__file__).resolve().parent.parent / "prompts/conflicts.md"
        ).read_text()
        return await self.structured(context, policy, ConflictReport)

    async def review_group(self, context):
        from .schema import GroupReview

        policy = (
            Path(__file__).resolve().parent.parent / "prompts/group-review.md"
        ).read_text()
        return await self.structured(context, policy, GroupReview, max_tokens=8000)

    async def structured(self, context, policy, schema, max_tokens=4000):
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
                            "name": "tarang_" + schema.__name__.lower(),
                            "strict": True,
                            "schema": schema.model_json_schema(),
                        },
                    },
                    "provider": {"require_parameters": True},
                    "max_tokens": max_tokens,
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

    async def download_voice(self, file_id, limit):
        info = await self.call("getFile", {"file_id": file_id})
        path = info.get("file_path", "")
        if (
            not isinstance(path, str)
            or not path
            or ".." in path
            or path.startswith("/")
            or not all(c.isalnum() or c in "_-/ ." for c in path)
            or " " in path
        ):
            raise RuntimeError("telegram_invalid_file")
        if info.get("file_size", 0) > limit:
            raise RuntimeError("telegram_file_too_large")
        async with httpx.AsyncClient(timeout=20) as client:
            async with client.stream(
                "GET", f"https://api.telegram.org/file/bot{self.token}/{path}"
            ) as response:
                if response.status_code != 200:
                    raise RuntimeError("telegram_file_error")
                content = bytearray()
                async for chunk in response.aiter_bytes():
                    content.extend(chunk)
                    if len(content) > limit:
                        raise RuntimeError("telegram_file_too_large")
        if not content:
            raise RuntimeError("telegram_empty_audio")
        return bytes(content)

    async def send_voice(self, chat, audio):
        async with httpx.AsyncClient(timeout=40) as client:
            response = await client.post(
                f"https://api.telegram.org/bot{self.token}/sendVoice",
                data={
                    "chat_id": str(chat),
                    "caption": "AI-generated Tarang voice. Full text and choices are in the chat.",
                },
                files={"voice": ("tarang.ogg", audio, "audio/ogg")},
            )
        if response.status_code != 200 or not response.json().get("ok"):
            raise RuntimeError("telegram_voice_error")
        return response.json()["result"]
