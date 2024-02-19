from aiogram import Dispatcher

from greetbot.routers import user, admin


def init_routers(dp: Dispatcher) -> None:
    routers = [
        user.router,
        admin.router
    ]

    dp.include_routers(*routers)