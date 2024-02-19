from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message
from loguru import logger

from greetbot.types.user import User


class UserDBMiddleware(BaseMiddleware):
    def __init__(self, check_admin: bool = False) -> None:
        self.check_admin = check_admin

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,  # type: ignore
        data: dict[str, Any]
    ) -> Any:
        user_db = await User.get(event.from_user.id)  # type: ignore
        if user_db is None:
            logger.error(f"User {event.from_user.id} not found")  # type: ignore
            return

        data["user_db"] = user_db

        if self.check_admin and not user_db.is_admin:
            logger.error(f"User {event.from_user.id} is not an admin")  # type: ignore
            return

        return await handler(event, data)
