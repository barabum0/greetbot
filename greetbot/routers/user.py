from aiogram import Router, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ChatJoinRequest, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from greetbot.types.greeting import Greeting
from greetbot.types.settings import settings
from greetbot.types.user import User

router = Router(name="User")


@router.chat_join_request()
async def chat_join(request: ChatJoinRequest, bot: Bot, state: FSMContext):
    db_user = await User.get(request.from_user.id)
    if not db_user:
        db_user = await User(id=request.from_user.id).insert()

    if settings.require_request_confirmation:
        await bot.send_message(request.from_user.id, settings.request_confirmation_message_text.replace("{{ channel_name }}", request.chat.full_name), reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=settings.request_confirmation_button_text,
                                                   callback_data=f"accept_request_{request.chat.id}")]]))
        return

    await request.approve()

    # TODO: сделать более простой метод + защиту от ошибок
    greetings = await Greeting.find(Greeting.is_enabled == True).to_list()
    for greeting in greetings:
        try:
            await greeting.send_as_aiogram_message(bot, request.from_user.id, request.from_user)
        except:
            pass


@router.callback_query(F.data.startswith("accept_request_"))
async def accept_request(call: CallbackQuery, bot: Bot, state: FSMContext):
    *_, chat_id = call.data.split("_")  # type: ignore

    # TODO: сделать более простой метод + защиту от ошибок
    greetings = await Greeting.find(Greeting.is_enabled == True).to_list()

    await bot.approve_chat_join_request(chat_id, call.from_user.id)
    await call.message.delete()  # type: ignore

    for greeting in greetings:
        try:
            await greeting.send_as_aiogram_message(bot, call.from_user.id, call.from_user)
        except:
            pass


@router.callback_query(F.data.startswith("survey_answer_"))
async def survey_answer(call: CallbackQuery, bot: Bot, state: FSMContext, user_db: User):
    _, _, greeting_id, answer_text = call.data.split("_", maxsplit=4)  # type: ignore

    greeting = await Greeting.get(greeting_id)
    if not greeting:
        await call.message.delete()
        return

    await call.message.delete()
    user_db.survey_answers[greeting.id] = answer_text
