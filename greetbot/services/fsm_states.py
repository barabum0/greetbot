from aiogram.fsm.state import State, StatesGroup


class AddGreeting(StatesGroup):
    awaiting_message = State()
