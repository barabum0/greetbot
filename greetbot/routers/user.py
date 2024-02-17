from aiogram import Router
from aiogram.types import ChatJoinRequest

from greetbot.types.user import ChannelUser

router = Router(name="User")


@router.chat_join_request()
async def chat_join(request: ChatJoinRequest):
    db_user = await ChannelUser.get(request.from_user.id)
    if not db_user:
        db_user = await ChannelUser(id=request.from_user.id).insert()

    await request.approve()
