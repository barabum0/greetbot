from aiogram.fsm.state import State, StatesGroup


class AddGreeting(StatesGroup):
    awaiting_message = State()


class Survey(StatesGroup):
    awaiting_variants = State()
    awaiting_message = State()


class EditGreeting(StatesGroup):
    awaiting_delay = State()
