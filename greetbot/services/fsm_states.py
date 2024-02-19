from aiogram.fsm.state import State, StatesGroup


class AddGreeting(StatesGroup):
    awaiting_caption = State()
    awaiting_media = State()
