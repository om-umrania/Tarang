"""Read-only sandbox readiness: authenticate and inspect payout balance.

No payout, debit, refund or booking is made. Never prints credentials, tokens,
account details or balance. Configure PINE_CLIENT_ID and PINE_CLIENT_SECRET
privately in .env. Successful authentication does not prove funding or authority.
"""

import asyncio
import sys
from pathlib import Path

import httpx
from dotenv import dotenv_values

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tarang.payments import UAT


async def main():
    values = dotenv_values(".env")
    cid, secret = values.get("PINE_CLIENT_ID"), values.get("PINE_CLIENT_SECRET")
    if not cid or not secret:
        print(
            "BLOCKED: configure Pine Labs sandbox client_id and client_secret privately."
        )
        return 2
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
            result = await client.post(
                UAT + "/api/auth/v1/token",
                json={
                    "client_id": cid,
                    "client_secret": secret,
                    "grant_type": "client_credentials",
                },
            )
            if result.status_code != 200:
                print("Sandbox authentication HTTP:", result.status_code)
                return 1
            token = result.json().get("access_token")
            if not isinstance(token, str) or not token:
                raise ValueError("invalid_token_response")
            balance = await client.get(
                UAT + "/payouts/v3/payments/funding-account",
                headers={"Authorization": "Bearer " + token},
            )
            if balance.status_code != 200:
                print("Sandbox payout balance HTTP:", balance.status_code)
                return 1
            amount = balance.json().get("balance")
            if (
                not isinstance(amount, dict)
                or amount.get("currency") != "INR"
                or not isinstance(amount.get("value"), int)
            ):
                raise ValueError("invalid_balance_response")
            print(
                "PASS: sandbox authentication and funding-account read. No payment made; sufficient test funding is not verified."
            )
            return 0
    except Exception as exc:
        print("Sandbox readiness failed:", type(exc).__name__)
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
