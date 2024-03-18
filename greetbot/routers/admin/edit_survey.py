from aiogram import Router, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, InaccessibleMessage
from aiogram.utils.formatting import Text, Pre
from aiogram_media_group import media_group_handler

from greetbot.routers.admin.main_menu import admin_start
from greetbot.services.fsm_states import Survey
from greetbot.types.greeting import Greeting
from greetbot.types.message import DatabaseMessage
from greetbot.types.survey import AnswerVariant
from greetbot.types.user import User

router = Router(name="Edit survey")


@router.callback_query(F.data.startswith("edit_surveys_list_"))
async def admin_edit_surveys_list(call: CallbackQuery, bot: Bot, user_db: User, state: FSMContext) -> None:
    *_, greeting_id = call.data.split("_")  # type: ignore
    greeting = await Greeting.get(greeting_id)
    if not greeting:
        return

    if not greeting.is_survey:
        return

    delete_after_answer_button = InlineKeyboardButton(
        text=f"{'[✅ Да]' if greeting.delete_survey_after_answer else '[❌ Нет]'} Удалять после ответа",
        callback_data=f"delete_after_answer__{greeting.id}_{'no' if greeting.delete_survey_after_answer else 'yes'}",
    )

    keyboard_buttons = [
        [InlineKeyboardButton(text=v.answer_text, callback_data=f"edit_survey__{greeting.id}_{v.answer_id}")] for v in
        greeting.survey_answer_variants
    ] + [[delete_after_answer_button]]
    keyboard_buttons.append([
        InlineKeyboardButton(text=f"📊 Заменить варианты", callback_data=f"make_a_survey_{greeting.id}"),
        InlineKeyboardButton(text=f"↩️ Назад", callback_data=f"back_to_start"),
    ])

    await call.message.edit_text('Выберите вариант ответа, чтобы его изменить', parse_mode="HTML",  # type: ignore
                                 reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons))  # type: ignore


@router.callback_query(F.data.startswith("delete_after_answer__"))
async def admin_set_delete_after_answer(call: CallbackQuery, bot: Bot, user_db: User, state: FSMContext) -> None:
    greeting_id, state = call.data.split("__")[1].split("_") # type: ignore
    greeting = await Greeting.get(greeting_id)
    if not greeting:
        return

    greeting.delete_survey_after_answer = (True if state == "yes" else False)
    await greeting.save()

    await admin_edit_surveys_list(call, bot, user_db, state)


@router.callback_query(F.data.startswith("edit_survey__"))
async def admin_edit_survey_answer(call: CallbackQuery, bot: Bot, user_db: User, state: FSMContext) -> None:
    greeting_id, answer_id, *_ = call.data.split("__")[1].split("_")  # type: ignore
    greeting = await Greeting.get(greeting_id)
    if not greeting:
        return

    if not greeting.is_survey:
        return

    answer = next((v for v in greeting.survey_answer_variants if v.answer_id == answer_id), None)
    if not answer:
        return

    keyboard_buttons = [
        [InlineKeyboardButton(
            text=f"💬 Удалить {index} 🗑️",
            callback_data=f"remove_reply_message__{greeting.id}_{answer.answer_id}_{index}",
        )] for index, message in enumerate(answer.reply_messages)
    ]
    keyboard_buttons.append([InlineKeyboardButton(text=f"➕ Добавить сообщение после ответа",
                                                  callback_data=f"add_reply_message_{greeting.id}_{answer.answer_id}")])
    keyboard_buttons.append([InlineKeyboardButton(text=f"🤖 Попробовать сообщения после ответа",
                                                  callback_data=f"try_reply_messages__{greeting.id}_{answer.answer_id}")])
    keyboard_buttons.append([InlineKeyboardButton(text=f"↩️ Назад", callback_data=f"back_to_start")])

    await call.message.edit_text(  # type: ignore
        text=f'Редактирование варианта ответа\n'
             f'<b>{answer.answer_text}</b>\n'
             f'\n'
             f'Меню\n'
             f'💬 - сообщения, которые будут присылаться после выбора варианта ответа\n' +
             (f'\n'.join(f"{index}. {message.settings_report}" for index, message in enumerate(answer.reply_messages))),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    )


@router.callback_query(F.data.startswith("try_reply_messages__"))
async def admin_try_reply_messages(call: CallbackQuery, bot: Bot, user_db: User, state: FSMContext) -> None:
    greeting_id, answer_id = call.data.split("__")[1].split("_")  # type: ignore
    greeting = await Greeting.get(greeting_id)
    if not greeting:
        return

    if not greeting.is_survey:
        return

    answer = next((v for v in greeting.survey_answer_variants if v.answer_id == answer_id), None)
    if not answer:
        return

    await call.message.delete()

    for reply_message in answer.reply_messages:
        await reply_message.send_as_aiogram_message(bot, call.from_user.id, call.from_user, test_case=True)

    await admin_start(call.message, bot, user_db, state, menu_only=True)


@router.callback_query(F.data.startswith("remove_reply_message__"))
async def admin_remove_reply_message(call: CallbackQuery, bot: Bot, user_db: User, state: FSMContext) -> None:
    greeting_id, answer_id, index = call.data.split("__")[1].split("_")  # type: ignore
    greeting = await Greeting.get(greeting_id)
    if not greeting:
        return

    if not greeting.is_survey:
        return

    answer = next((v for v in greeting.survey_answer_variants if v.answer_id == answer_id), None)
    if not answer:
        return
    answer_index = greeting.survey_answer_variants.index(answer)
    greeting.survey_answer_variants[answer_index].reply_messages.pop(index)

    await greeting.save()

    await admin_edit_survey_answer(call, bot, user_db, state)


@router.callback_query(F.data.startswith("add_reply_message_"))
async def admin_add_survey_answer_reply_message(call: CallbackQuery, bot: Bot, user_db: User,
                                                state: FSMContext) -> None:
    *_, greeting_id, answer_id = call.data.split("_")  # type: ignore
    greeting = await Greeting.get(greeting_id)
    if not greeting:
        return

    if not greeting.is_survey:
        return

    answer = next((v for v in greeting.survey_answer_variants if v.answer_id == answer_id), None)
    if not answer:
        return

    await call.message.delete()
    await call.message.answer(
        f"Пришлите ваше сообщение, отправляемое после ответа. Это может быть текст, фото, видео и документы.")

    await state.set_state(Survey.awaiting_message)
    await state.set_data({"greeting_id": greeting.id, "answer_id": answer_id})


async def process_add_reply(messages: list[Message], bot: Bot, user_db: User, state: FSMContext) -> None:
    state_data = await state.get_data()
    greeting_id = state_data["greeting_id"]
    answer_id = state_data["answer_id"]

    greeting = await Greeting.get(greeting_id)
    if not greeting:
        return

    if not greeting.is_survey:
        return

    answer = next((v for v in greeting.survey_answer_variants if v.answer_id == answer_id), None)
    if not answer:
        return
    answer_index = greeting.survey_answer_variants.index(answer)

    reply_message = await DatabaseMessage.from_messages(messages, bot)

    greeting.survey_answer_variants[answer_index].reply_messages.append(reply_message)
    await greeting.save()

    await state.set_state()


@router.message(Survey.awaiting_message, F.media_group_id)
@media_group_handler
async def admin_add_reply_message_media_group(messages: list[Message], bot: Bot, user_db: User,
                                              state: FSMContext) -> None:
    await process_add_reply(messages, bot, user_db, state)
    await admin_start(messages[0], bot, user_db, state, menu_only=True)


@router.message(Survey.awaiting_message)
async def admin_add_reply_message_media_not_media_group(message: Message, bot: Bot, user_db: User,
                                                        state: FSMContext) -> None:
    await process_add_reply([message], bot, user_db, state)
    await admin_start(message, bot, user_db, state, menu_only=True)
