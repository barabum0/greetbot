from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from greetbot.types.greeting import Greeting
from greetbot.types.settings import settings
from greetbot.types.user import User

router = Router(name="Main menu")


@router.message(Command("start"))
async def admin_start(message: Message, bot: Bot, user_db: User, state: FSMContext, menu_only: bool = False) -> None:
    await state.set_state()

    if not menu_only:
        await message.answer("Здравствуйте! Вы попали в меню редактирования приветствий.")
        if settings.show_credits:
            await message.answer("<i>bot created by @barabumbum</i>")

    keyboard_buttons: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text="🛠️ Настроить приветствия", callback_data="edit_greetings")]
        # TODO: добавить статистику
    ]

    if await Greeting.count() != 0:
        keyboard_buttons.append(
            [InlineKeyboardButton(text="🏁 Проверить действие приветствия", callback_data="try_greeting")])

    await message.answer("<b>Выберите действие:</b>",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons))


@router.callback_query(F.data == "back_to_start")
async def admin_back_to_start(call: CallbackQuery, bot: Bot, user_db: User, state: FSMContext) -> None:
    await call.message.delete()  # type: ignore
    await admin_start(call.message, bot, user_db, state, menu_only=True)


@router.callback_query(F.data == "try_greeting")
async def admin_try_greeting(call: CallbackQuery, bot: Bot, user_db: User, state: FSMContext) -> None:
    await call.message.delete()  # type: ignore

    # TODO: сделать более простой метод + защиту от ошибок
    greetings = await Greeting.find(Greeting.is_enabled == True).to_list()
    for greeting in greetings:
        await greeting.send_as_aiogram_message(bot, user_db.id, call.from_user, test_case=True)

    await admin_start(call.message, bot, user_db, state, menu_only=True)


@router.callback_query(F.data == "edit_greetings")
async def admin_edit_greetings(call: CallbackQuery, bot: Bot, user_db: User) -> None:
    greetings = await Greeting.find(Greeting.is_enabled == True).to_list()
    text = "\n\n".join([f"{index}) {greeting.settings_report}" for index, greeting in enumerate(greetings)])

    text += "\n\n\n<b>Выберите действие:</b>"
    text = text.strip()

    keyboard_buttons: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text=f"📄 Редактировать приветствие {index}",
                              callback_data=f"edit_greeting_{greeting.id}")]
        for index, greeting in enumerate(greetings)
    ]

    keyboard_buttons.append([InlineKeyboardButton(text=f"➕ Добавить приветствие", callback_data=f"add_greeting")])
    keyboard_buttons.append([InlineKeyboardButton(text=f"↩️ Назад", callback_data=f"back_to_start")])

    await call.answer()
    await call.message.edit_text(text, parse_mode="HTML",  # type: ignore
                                 reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons))  # type: ignore
