from aiogram import Router
from aiogram.types import ChatJoinRequest
from loguru import logger

router = Router(name="User")


@router.chat_join_request()
async def chat_join(request: ChatJoinRequest):
    logger.info("User {user} requested", user=request.from_user.username)
