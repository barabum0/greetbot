from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup
from aiogram_media_group import media_group_handler, MediaGroupFilter
from loguru import logger

from greetbot.services.fsm_states import AddGreeting
from greetbot.services.middlewares.user import UserDBMiddleware
from greetbot.types.greeting import Greeting, MediaFile, MediaDataType
from greetbot.types.extra.file import Base64File
from greetbot.types.settings import settings
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
        await greeting.send_as_aiogram_message(bot, user_db.id, call.from_user)

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


@router.callback_query(F.data == "add_greeting")
async def admin_add_greeting(call: CallbackQuery, bot: Bot, user_db: User, state: FSMContext) -> None:
    await state.set_state(AddGreeting.awaiting_caption)
    # TODO: парсинг сообщений напрямую
    buttons: list[list[KeyboardButton]] = [
        [KeyboardButton(text="/no_caption")]
    ]
    await call.message.delete()  # type: ignore
    await call.message.answer(  # type: ignore
        f"Введите текст вашего будущего приветствие"
        f"\n<i><code>/no_caption</code> чтобы текста не было</i>",
        reply_markup=ReplyKeyboardMarkup(keyboard=buttons, one_time_keyboard=True)
    )


@router.message(AddGreeting.awaiting_caption)
async def admin_add_greeting_name(message: Message, bot: Bot, user_db: User, state: FSMContext) -> None:
    if any((
            not message.text,
            message.caption is not None,
            message.photo is not None,
            message.video is not None,
            message.document is not None
    )):
        await message.delete()
        await message.answer(f"Отправьте только текст")
        return

    buttons: list[list[KeyboardButton]] = [
        [KeyboardButton(text="/no_media")]
    ]

    await message.answer(
        f"Теперь отправьте нужные фото, документы и видео <b>одним сообщением</b>"
        f"\n<i>текст, аудио и всё, кроме видео, документов и изображений будет игнорироваться</i>"
        f"\n<i><code>/no_media</code> для того, чтобы медиа не было</i>",
        reply_markup=ReplyKeyboardMarkup(keyboard=buttons, one_time_keyboard=True)
    )
    data = {
        "caption": message.html_text if not message.text.startswith("/no_caption") else None  # type: ignore
    }
    await state.set_state(AddGreeting.awaiting_media)
    await state.set_data(data)


@router.message(AddGreeting.awaiting_media, (~F.text & F.media_group_id))
@media_group_handler
async def admin_add_greeting_media(messages: list[Message], bot: Bot, user_db: User, state: FSMContext) -> None:
    logger.info("Caught a media group")
    media_files: list[MediaFile] = []
    for message in messages:
        if message.photo is not None:
            data = await bot.download(message.photo[-1].file_id)
            data_bytes = data.read()  # type: ignore
            media_files.append(MediaFile(data_type=MediaDataType.IMAGE, base64=Base64File.from_bytes(data_bytes)))
        elif message.video is not None:
            data = await bot.download(message.video.file_id)
            data_bytes = data.read()  # type: ignore
            media_files.append(MediaFile(data_type=MediaDataType.VIDEO, base64=Base64File.from_bytes(data_bytes)))
        elif message.document is not None:
            data = await bot.download(message.document.file_id)
            data_bytes = data.read()  # type: ignore
            media_files.append(MediaFile(data_type=MediaDataType.DOCUMENT, base64=Base64File.from_bytes(data_bytes), file_name=message.document.file_name or "file.txt"))

    state_data = await state.get_data()
    logger.debug(state_data)
    if state_data.get("caption", None) is None and len(media_files) == 0:
        await messages[-1].answer(f"Если в сообщении нету текста, там обязательно должны быть фотографии, видео или документ")
        return

    greeting = Greeting(caption=state_data.get("caption", None), media_files=media_files)

    await messages[-1].answer(f"Отлично! Вот ваше новое приветствие:")
    await greeting.send_as_aiogram_message(bot, messages[-1].chat.id, messages[-1].from_user)

    state_data = {"greeting": greeting}
    await state.set_data(state_data)

    keyboard_buttons: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text="✅ Сохранить", callback_data="save_greeting")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_greeting")]
    ]
    await messages[-1].answer(f"<b>Как вам?</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons))
    await state.set_state()


@router.message(AddGreeting.awaiting_media)
async def admin_add_greeting_media_not_media_group(message: Message, bot: Bot, user_db: User, state: FSMContext) -> None:
    logger.info("Caught a single message")
    if message.text is not None:
        if not message.text.startswith("/no_media"):
            await message.answer("Отправьте фото, видео или документ!")
            return
        logger.info("Caught a /no_media")

    media_files = []
    if message.text is not None and message.text.startswith("/no_media"):
        pass
    elif message.text is None:
        photo = None
        if message.photo is not None:
            photo = message.photo[-1]

        media = photo or message.video or message.document
        if not media and not message.text.startswith("/no_media"):  # type: ignore
            await message.answer("Отправьте фото, видео или документ!")
            return

        if photo:
            media_type = MediaDataType.IMAGE
        elif message.document:
            media_type = MediaDataType.DOCUMENT
        else:
            media_type = MediaDataType.VIDEO

        data = await bot.download(media.file_id)  # type: ignore
        data_bytes = data.read()  # type: ignore
        media_file = MediaFile(data_type=media_type, base64=Base64File.from_bytes(data_bytes))

        if message.document:
            media_file.file_name = message.document.file_name or "file.txt"

        media_files.append(media_file)

    state_data = await state.get_data()
    logger.debug(state_data)
    if state_data.get("caption", None) is None and len(media_files) == 0:
        await message.answer(f"Если в сообщении нету текста, там обязательно должны быть фотографии, видео или документ")
        return

    greeting = Greeting(caption=state_data.get("caption", None), media_files=media_files)

    await message.answer(f"Отлично! Вот ваше новое приветствие:")
    await greeting.send_as_aiogram_message(bot, message.chat.id, message.from_user)

    state_data = {"greeting": greeting}
    await state.set_data(state_data)

    keyboard_buttons: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text="✅ Сохранить", callback_data="save_greeting")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_greeting")]
    ]
    await message.answer(f"<b>Как вам?</b>",
                              reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons))
    await state.set_state()
    return



@router.callback_query(F.data == "save_greeting")
async def admin_save_greeting(call: CallbackQuery, bot: Bot, user_db: User, state: FSMContext) -> None:
    state_data = await state.get_data()
    if (greeting := state_data.get("greeting", None)) is not None:
        await greeting.insert()

    await call.message.delete()  # type: ignore
    await admin_start(call.message, bot, user_db, state, menu_only=True)
