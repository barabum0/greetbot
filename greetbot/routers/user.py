from aiogram import Router, Bot, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import ChatJoinRequest, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, \
    ReplyKeyboardMarkup, KeyboardButton, Message
from aiogram.utils.deep_linking import create_start_link
from loguru import logger

from greetbot.services.middlewares.user import UserDBMiddleware
from greetbot.types.greeting import Greeting
from greetbot.types.settings import settings
from greetbot.types.user import User

router = Router(name="User")
router.message.middleware(UserDBMiddleware(check_admin=False))
router.callback_query.middleware(UserDBMiddleware(check_admin=False))


@router.chat_join_request()
async def chat_join(request: ChatJoinRequest, bot: Bot, state: FSMContext):
    await state.set_data({"chat_id": request.chat.id})
    db_user = await User.get(request.from_user.id)
    if not db_user:
        db_user = await User(id=request.from_user.id, username=request.from_user.username).insert()

    if settings.require_request_confirmation:
        await state.set_data({"chat_id": request.chat.id})

        message = await bot.send_message(
            request.from_user.id,
            settings.request_confirmation_message_text.replace("{{ channel_name }}",
                                                               request.chat.full_name),
        )
        await message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(
                    text=settings.request_confirmation_button_text,
                    url=await create_start_link(bot, f"{request.chat.id}_{message.message_id}"))]]))
        return

    try:
        await request.approve()
    except TelegramBadRequest:
        pass

    # TODO: сделать более простой метод + защиту от ошибок
    greetings = await Greeting.find(Greeting.is_enabled == True).to_list()
    for greeting in greetings:
        try:
            await greeting.send_as_aiogram_message(bot, request.from_user.id, request.from_user)
        except:
            pass


@router.message(CommandStart(deep_link=True))
async def accept_request(message: Message, bot: Bot, state: FSMContext, command: CommandObject):
    chat_id, message_id = command.args.split("_")

    try:
        await bot.delete_message(message.chat.id, message_id)
    except:
        pass

    try:
        await bot.approve_chat_join_request(int(chat_id), message.from_user.id)
    except TelegramBadRequest as e:
        logger.warning("Failed to accept chat join request. {e}", e=e.message)
        return

    # TODO: сделать более простой метод + защиту от ошибок
    greetings = await Greeting.find(Greeting.is_enabled == True).to_list()

    for greeting in greetings:
        try:
            await greeting.send_as_aiogram_message(bot, message.from_user.id, message.from_user)
        except Exception as e:
            logger.exception(e)


@router.callback_query(F.data.startswith("survey_answer_"))
async def survey_answer(call: CallbackQuery, bot: Bot, state: FSMContext, user_db: User):
    _, _, greeting_id, answer_id = call.data.split("_", maxsplit=4)  # type: ignore

    greeting = await Greeting.get(greeting_id)
    if not greeting:
        await call.message.delete()
        return

    variant = next((v for v in greeting.survey_answer_variants if v.answer_id == answer_id), None)
    if variant is None:
        if greeting.delete_survey_after_answer:
            await call.message.delete()
        return

    if greeting.delete_survey_after_answer:
        await call.message.delete()
    user_db.survey_answers[greeting.id] = variant.answer_text
    await user_db.save()

    for message in variant.reply_messages:
        await message.send_as_aiogram_message(bot, call.from_user.id, call.from_user)
