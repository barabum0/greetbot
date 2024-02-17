from aiogram import Dispatcher

from greetbot.routers import user


def init_routers(dp: Dispatcher) -> None:
    routers = [
        user.router
    ]

    dp.include_routers(*routers)