from typing import Any

from aiogram.types import User


def apply_user_info(user: User, text: str | None) -> str | None:
    if text is None:
        return text
    placeholders: dict[str, Any] = {
        "user_id": user.id,
        "name": user.full_name,
        "first_name": user.first_name,
        "last_name": user.last_name
    }
    for key, value in placeholders.items():
        text = text.replace("{{ " + str(key) + " }}", str(value))
    return text