from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, KeyboardButton, \
    ReplyKeyboardMarkup, InaccessibleMessage
from aiogram.utils.formatting import Pre, Text
from aiogram_media_group import media_group_handler
from loguru import logger

from greetbot.services.fsm_states import AddGreeting, Survey
from greetbot.services.middlewares.user import UserDBMiddleware
from greetbot.types.greeting import Greeting
from greetbot.types.extra.file import Base64File
from greetbot.types.media import MediaFile, MediaDataType
from greetbot.types.settings import settings
from greetbot.types.survey import AnswerVariant
from greetbot.types.user import User

router = Router(name="User")
router.message.middleware(UserDBMiddleware(check_admin=True))
router.callback_query.middleware(UserDBMiddleware(check_admin=True))


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


@router.callback_query(F.data.startswith("edit_greeting_"))
async def admin_edit_greeting(call: CallbackQuery, bot: Bot, user_db: User, state: FSMContext) -> None:
    *_, greeting_id = call.data.split("_")  # type: ignore
    greeting = await Greeting.get(greeting_id)
    if not greeting:
        return

    keyboard_buttons: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text=f"🗑️ Удалить приветствие",
                              callback_data=f"delete_greeting_{greeting.id}")],
        [InlineKeyboardButton(text=f"↩️ Назад", callback_data=f"back_to_start")]
    ]
    if not greeting.is_survey and len(greeting.media_files) == 0:
        keyboard_buttons.insert(0, [InlineKeyboardButton(text=f"📊 Сделать опросом",
                                                         callback_data=f"make_a_survey_{greeting.id}")])
    elif greeting.is_survey:
        keyboard_buttons.insert(0, [InlineKeyboardButton(text=f"❌ Убрать опрос",
                                                         callback_data=f"remove_survey_{greeting.id}")])

    await call.message.edit_text('Что хотите сделать с приветствием?', parse_mode="HTML",  # type: ignore
                                 reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons))  # type: ignore


@router.callback_query(F.data.startswith("delete_greeting_"))
async def admin_delete_greeting(call: CallbackQuery, bot: Bot, user_db: User, state: FSMContext) -> None:
    *_, greeting_id = call.data.split("_")  # type: ignore
    greeting = await Greeting.get(greeting_id)
    if not greeting:
        return

    await greeting.delete()

    await call.message.delete()  # type: ignore
    await admin_start(call.message, bot, user_db, state)


@router.callback_query(F.data.startswith("remove_survey_"))
async def admin_remove_survey(call: CallbackQuery, bot: Bot, user_db: User, state: FSMContext) -> None:
    *_, greeting_id = call.data.split("_")  # type: ignore
    greeting = await Greeting.get(greeting_id)
    if not greeting:
        return

    greeting.survey_answer_variants = []
    greeting.is_survey = False
    await greeting.save()
    await admin_edit_greeting(call, bot, user_db, state)


@router.callback_query(F.data.startswith("make_a_survey_"))
async def admin_make_a_survey(call: CallbackQuery, bot: Bot, user_db: User, state: FSMContext) -> None:
    *_, greeting_id = call.data.split("_")  # type: ignore
    greeting = await Greeting.get(greeting_id)
    if not greeting:
        return

    if call.message is None or isinstance(call.message, InaccessibleMessage):
        return

    await call.message.delete()
    await call.message.answer(Text(f"Пришлите варианты ответа для вашего будущего опроса в подобном формате:\n",
                                   Pre('Я новичек\nЯ бывалый\nЯ мамкин криптоинвестор со стажем',
                                       language='опрос')).as_html())

    state_data = {"greeting_id": greeting.id}
    await state.set_data(state_data)
    await state.set_state(Survey.awaiting_variants)


@router.message(Survey.awaiting_variants, F.text)
async def admin_make_a_survey_variants(message: Message, bot: Bot, user_db: User,
                                       state: FSMContext) -> None:
    data = await state.get_data()
    greeting = await Greeting.get(data.get("greeting_id"))
    if not greeting:
        return

    variants = message.text.split("\n")
    greeting.survey_answer_variants = [AnswerVariant(answer_text=v) for v in variants]
    greeting.is_survey = True
    await greeting.save()
    await greeting.send_as_aiogram_message(bot, user_db.id, message.from_user, test_case=True)
    await admin_start(message, bot, user_db, state, menu_only=True)


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
