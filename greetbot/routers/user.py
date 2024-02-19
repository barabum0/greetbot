from aiogram import Router, Bot
from aiogram.types import ChatJoinRequest

from greetbot.types.bot_config import Greeting
from greetbot.types.user import User

router = Router(name="User")


@router.chat_join_request()
async def chat_join(request: ChatJoinRequest, bot: Bot):
    db_user = await User.get(request.from_user.id)
    if not db_user:
        db_user = await User(id=request.from_user.id).insert()

    await request.approve()

    # TODO: сделать более простой метод + защиту от ошибок
    greetings = await Greeting.find(Greeting.is_enabled == True).to_list()
    for greeting in greetings:
        try:
            await greeting.send_as_aiogram_message(bot, request.from_user.id)
        except:
            pass
