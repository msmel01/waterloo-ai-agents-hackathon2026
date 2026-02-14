"""Auth router for Clerk webhook handling."""

import logging
import re
import uuid
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Body, Depends, Header, HTTPException, Request
from svix.webhooks import Webhook, WebhookVerificationError

from src.core.config import config
from src.core.container import Container as DIContainer
from src.repository.heart_repository import HeartRepository
from src.schemas.auth_schema import ClerkWebhookEventRequest
from src.schemas.common_schema import ErrorResponse, SuccessResponse

router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger(__name__)


def _extract_primary_email(clerk_data: dict) -> str | None:
    """Extract the primary email from Clerk webhook payload."""
    email_addresses = clerk_data.get("email_addresses", [])
    primary_email_id = clerk_data.get("primary_email_address_id")
    for email_record in email_addresses:
        if email_record.get("id") == primary_email_id:
            return email_record.get("email_address")
    if email_addresses:
        return email_addresses[0].get("email_address")
    return None


def _build_display_name(clerk_data: dict) -> str:
    """Build display name from Clerk payload."""
    first_name = clerk_data.get("first_name") or ""
    last_name = clerk_data.get("last_name") or ""
    full_name = f"{first_name} {last_name}".strip()
    if full_name:
        return full_name
    username = clerk_data.get("username")
    if username:
        return username
    return "Heart User"


def _slugify(value: str) -> str:
    """Create URL-safe slug chunk."""
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return normalized or "heart"


@router.post(
    "/webhook",
    response_model=SuccessResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid webhook signature."},
        500: {"model": ErrorResponse, "description": "Unexpected processing error."},
    },
)
@inject
async def clerk_webhook(
    request: Request,
    svix_id: Annotated[str, Header(alias="svix-id")],
    svix_timestamp: Annotated[str, Header(alias="svix-timestamp")],
    svix_signature: Annotated[str, Header(alias="svix-signature")],
    webhook_payload: ClerkWebhookEventRequest = Body(...),
    heart_repository: HeartRepository = Depends(Provide[DIContainer.heart_repository]),
):
    """Verify Clerk Svix signature and synchronize heart records for user lifecycle events."""
    webhook_secret = config.CLERK_WEBHOOK_SECRET_VALUE
    if not webhook_secret:
        logger.warning("CLERK_WEBHOOK_SECRET is not set, ignoring webhook")
        return SuccessResponse(message="Webhook secret not configured; event ignored.")

    payload = await request.body()
    headers = {
        "svix-id": svix_id,
        "svix-timestamp": svix_timestamp,
        "svix-signature": svix_signature,
    }

    try:
        wh = Webhook(webhook_secret)
        evt = wh.verify(payload, headers)
    except WebhookVerificationError as e:
        logger.error(f"Webhook verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = evt.get("type")
    data = evt.get("data")
    _ = webhook_payload

    if event_type in ["user.created", "user.updated"]:
        user_id = data.get("id")
        email = _extract_primary_email(data) or f"{user_id}@clerk.local"
        display_name = _build_display_name(data)

        if user_id:
            heart = await heart_repository.find_by_clerk_id(user_id)
            if heart:
                heart.email = email
                heart.display_name = display_name
                await heart_repository.update(heart.id, heart)
            else:
                slug = f"{_slugify(display_name)}-{uuid.uuid4().hex[:8]}"
                await heart_repository.create(
                    heart_repository.model(
                        clerk_user_id=user_id,
                        email=email,
                        display_name=display_name,
                        persona={
                            "traits": [],
                            "vibe": "",
                            "tone": "",
                            "humor_level": 0,
                        },
                        expectations={
                            "dealbreakers": [],
                            "green_flags": [],
                            "must_haves": [],
                        },
                        shareable_slug=slug,
                        is_active=True,
                    )
                )

    elif event_type == "user.deleted":
        user_id = data.get("id")
        if user_id:
            await heart_repository.delete_by_clerk_id(user_id)

    return SuccessResponse(message=f"Webhook processed: {event_type}")
