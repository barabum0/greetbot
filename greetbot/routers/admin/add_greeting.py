from aiogram import Router, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, InaccessibleMessage
from aiogram_media_group import media_group_handler

from greetbot.routers.admin.main_menu import admin_start
from greetbot.services.fsm_states import AddGreeting
from greetbot.types.greeting import Greeting
from greetbot.types.user import User

router = Router(name="Add greeting")


@router.callback_query(F.data == "add_greeting")
async def admin_add_greeting(call: CallbackQuery, bot: Bot, user_db: User, state: FSMContext) -> None:
    await state.set_state(AddGreeting.awaiting_message)

    if call.message is None or isinstance(call.message, InaccessibleMessage):
        return

    await call.message.delete()
    await call.message.answer(f"Пришлите ваше будущее приветствие. Это может быть текст, фото, видео и документы.")


async def process_add_greeting(messages: list[Message], bot: Bot, user_db: User, state: FSMContext) -> None:
    greeting = await Greeting.from_messages(messages, bot)
    await messages[-1].answer(f"Отлично! Вот ваше новое приветствие:")
    await greeting.send_as_aiogram_message(bot, messages[-1].chat.id, messages[-1].from_user)

    state_data = {"greeting": greeting}
    await state.set_data(state_data)

    keyboard_buttons: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text="✅ Сохранить", callback_data="save_greeting")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="back_to_start")]
    ]
    await messages[-1].answer(f"<b>Cохраняем?</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons))
    await state.set_state()


@router.message(AddGreeting.awaiting_message, F.media_group_id)
@media_group_handler
async def admin_add_message_media_group(messages: list[Message], bot: Bot, user_db: User, state: FSMContext) -> None:
    await process_add_greeting(messages, bot, user_db, state)


@router.message(AddGreeting.awaiting_message)
async def admin_add_greeting_media_not_media_group(message: Message, bot: Bot, user_db: User,
                                                   state: FSMContext) -> None:
    await process_add_greeting([message], bot, user_db, state)


@router.callback_query(F.data == "save_greeting")
async def admin_save_greeting(call: CallbackQuery, bot: Bot, user_db: User, state: FSMContext) -> None:
    state_data = await state.get_data()
    if (greeting := state_data.get("greeting", None)) is not None:
        await greeting.insert()

    await call.message.delete()  # type: ignore
    await admin_start(call.message, bot, user_db, state, menu_only=True)