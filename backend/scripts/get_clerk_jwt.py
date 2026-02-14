"""Fetch a Clerk JWT for local API testing.

Usage examples:
    python scripts/get_clerk_jwt.py --email you@example.com
    python scripts/get_clerk_jwt.py --user-id user_123
    python scripts/get_clerk_jwt.py --email you@example.com --expires 3600

Requires:
    CLERK_SECRET_KEY in environment
    A Clerk JWT template in dashboard (passed via --template)
"""

from __future__ import annotations

import argparse
import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()
CLERK_API_BASE = "https://api.clerk.com/v1"


def _headers(secret_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/json",
    }


def _find_user_id_by_email(client: httpx.Client, email: str) -> str:
    # Clerk supports query arrays; try common variants for compatibility.
    candidates = []
    params_list = [
        {"email_address": email, "limit": 10},
        {"email_address[]": email, "limit": 10},
    ]
    for params in params_list:
        resp = client.get(f"{CLERK_API_BASE}/users", params=params)
        resp.raise_for_status()
        payload = resp.json()
        users = payload if isinstance(payload, list) else payload.get("data", [])
        if users:
            candidates = users
            break

    if not candidates:
        raise RuntimeError(f"No Clerk user found for email: {email}")

    return candidates[0]["id"]


def _list_sessions_for_user(client: httpx.Client, user_id: str) -> list[dict]:
    """Fetch sessions for a user and return active/pending first."""
    resp = client.get(
        f"{CLERK_API_BASE}/sessions",
        params={"user_id": user_id, "limit": 50},
    )
    resp.raise_for_status()
    payload = resp.json()
    sessions = payload if isinstance(payload, list) else payload.get("data", [])

    # Prefer active/pending sessions.
    preferred = [s for s in sessions if s.get("status") in {"active", "pending"}]
    return preferred or sessions


def _create_token_from_session(
    client: httpx.Client,
    session_id: str,
    expires: int,
    template: str,
) -> str:
    body: dict[str, object] = {"expires_in_seconds": expires}
    resp = client.post(
        f"{CLERK_API_BASE}/sessions/{session_id}/tokens/{template}",
        json=body,
    )
    resp.raise_for_status()
    data = resp.json()
    token = data.get("jwt")
    if not token:
        raise RuntimeError(f"Unexpected Clerk token response: {data}")
    return token


def main() -> int:
    parser = argparse.ArgumentParser(description="Get Clerk JWT for API testing")
    parser.add_argument("--email", help="Clerk user email")
    parser.add_argument("--user-id", help="Clerk user id, e.g. user_...")
    parser.add_argument(
        "--expires",
        type=int,
        default=3600,
        help="Token TTL in seconds (default: 3600)",
    )
    parser.add_argument("--template", required=True, help="Clerk JWT template name")
    args = parser.parse_args()

    if not args.email and not args.user_id:
        parser.error("Provide either --email or --user-id")

    secret_key = os.getenv("CLERK_SECRET_KEY")
    if not secret_key:
        print("Error: CLERK_SECRET_KEY is not set", file=sys.stderr)
        return 1

    with httpx.Client(headers=_headers(secret_key), timeout=20.0) as client:
        user_id = args.user_id or _find_user_id_by_email(client, args.email)
        sessions = _list_sessions_for_user(client, user_id)
        if not sessions:
            raise RuntimeError(
                f"No sessions found for user {user_id}. Sign in once to create a session."
            )
        session_id = sessions[0]["id"]
        token = _create_token_from_session(
            client=client,
            session_id=session_id,
            expires=args.expires,
            template=args.template,
        )

    print(token)
    print("\n# helper:")
    print(f'export SUITOR_JWT="{token}"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
