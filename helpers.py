from http import HTTPStatus

import jwt
from fastapi import HTTPException

from lnbits.helpers import create_access_token
from lnbits.settings import settings


def create_api_key(inventory_id: str, service_id: str) -> str:
    """Generate a new API key for external services."""
    api_key = create_access_token(
        {
            "inventory_id": inventory_id,
            "service_id": service_id,
        }
    )
    return api_key


def extract_token_payload(token: str):
    try:
        payload: dict = jwt.decode(token, settings.auth_secret_key, ["HS256"])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid token."
        ) from None


def check_item_tags(service_allowed_tags: list[str], item_tags: list[str]) -> bool:
    if service_allowed_tags == []:
        return True
    return any(tag in service_allowed_tags for tag in item_tags)


def split_tags(tags: str | None) -> list[str]:
    if not tags:
        return []
    return [tag.strip() for tag in tags.split(",") if tag.strip()]
