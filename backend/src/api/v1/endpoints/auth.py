"""Auth router for Clerk webhook handling (Suitor sync)."""

import logging

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from svix.webhooks import Webhook, WebhookVerificationError

from src.core.config import config
from src.core.container import Container
from src.repository.suitor_repository import SuitorRepository
from src.schemas.common_schema import SuccessResponse

router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger(__name__)


def _extract_primary_email(clerk_data: dict) -> str | None:
    email_addresses = clerk_data.get("email_addresses", [])
    primary_email_id = clerk_data.get("primary_email_address_id")
    for email_record in email_addresses:
        if email_record.get("id") == primary_email_id:
            return email_record.get("email_address")
    if email_addresses:
        return email_addresses[0].get("email_address")
    return None


def _build_name(clerk_data: dict) -> str:
    first_name = clerk_data.get("first_name") or ""
    last_name = clerk_data.get("last_name") or ""
    full_name = f"{first_name} {last_name}".strip()
    if full_name:
        return full_name
    username = clerk_data.get("username")
    return username or "Suitor"


@router.post("/webhook", response_model=SuccessResponse)
@inject
async def clerk_webhook(
    request: Request,
    svix_id: str = Header(alias="svix-id"),
    svix_timestamp: str = Header(alias="svix-timestamp"),
    svix_signature: str = Header(alias="svix-signature"),
    suitor_repo: SuitorRepository = Depends(Provide[Container.suitor_repository]),
):
    """Verify Clerk Svix signature and sync user lifecycle events into suitors table."""
    webhook_secret = config.CLERK_WEBHOOK_SECRET_VALUE
    if not webhook_secret:
        raise HTTPException(
            status_code=500, detail="CLERK_WEBHOOK_SECRET is not configured"
        )

    payload = await request.body()
    headers = {
        "svix-id": svix_id,
        "svix-timestamp": svix_timestamp,
        "svix-signature": svix_signature,
    }

    try:
        event = Webhook(webhook_secret).verify(payload, headers)
    except WebhookVerificationError as exc:
        logger.error("Webhook verification failed: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    event_type = event.get("type")
    data = event.get("data") or {}
    user_id = data.get("id")

    if not user_id:
        return SuccessResponse(message="Webhook ignored: missing user id")

    if event_type == "user.created":
        existing = await suitor_repo.find_by_clerk_id(user_id)
        if not existing:
            await suitor_repo.create(
                suitor_repo.model(
                    clerk_user_id=user_id,
                    email=_extract_primary_email(data),
                    name=_build_name(data),
                )
            )

    elif event_type == "user.updated":
        await suitor_repo.update_by_clerk_id(
            user_id,
            {
                "email": _extract_primary_email(data),
                "name": _build_name(data),
            },
        )

    elif event_type == "user.deleted":
        await suitor_repo.delete_by_clerk_id(user_id)

    return SuccessResponse(message="ok")
