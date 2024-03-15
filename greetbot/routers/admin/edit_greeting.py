from aiogram import Router, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, InaccessibleMessage
from aiogram.utils.formatting import Text, Pre

from greetbot.routers.admin.main_menu import admin_start
from greetbot.services.fsm_states import Survey
from greetbot.types.greeting import Greeting
from greetbot.types.survey import AnswerVariant
from greetbot.types.user import User

router = Router(name="Edit greeting")


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
    variants = message.text.split("\n")

    if any(len(v) >= 20 for v in variants):
        await message.answer("Длина одного варианта ответа должна быть не более 20 символов")
        return

    data = await state.get_data()
    greeting = await Greeting.get(data.get("greeting_id"))
    if not greeting:
        return

    greeting.survey_answer_variants = [AnswerVariant(answer_text=v) for v in variants]
    greeting.is_survey = True
    await greeting.save()
    await greeting.send_as_aiogram_message(bot, user_db.id, message.from_user, test_case=True)
    await admin_start(message, bot, user_db, state, menu_only=True)