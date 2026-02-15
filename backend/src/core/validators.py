import bleach
from fastapi import HTTPException


class PasswordValidationError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)


def validate_password(password: str) -> bool:
    if len(password) < 8:
        raise PasswordValidationError("Password must be at least 8 characters long")
    if not any(char.isupper() for char in password):
        raise PasswordValidationError(
            "Password must contain at least one uppercase letter"
        )
    if not any(char.islower() for char in password):
        raise PasswordValidationError(
            "Password must contain at least one lowercase letter"
        )
    return True


def sanitize_input(text: str | None) -> str | None:
    """Strip HTML/script content from user text input."""
    if text is None:
        return None
    if bleach is not None:
        return bleach.clean(text, tags=[], strip=True).strip()

    # Fallback when bleach is unavailable.
    import re

    cleaned = re.sub(r"<[^>]*>", "", text)
    return cleaned.strip()
