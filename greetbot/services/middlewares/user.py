from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message

from greetbot.types.user import User


class UserDBMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.counter = 0

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,  # type: ignore
        data: dict[str, Any]
    ) -> Any:
        user_db = await User.get(event.from_user.id)  # type: ignore
        data["user_db"] = user_db

        return await handler(event, data)
