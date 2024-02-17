import asyncio

from aiogram import Dispatcher, Bot

from greetbot.routers import init_routers
from greetbot.services.database import init_database
from greetbot.services.logs import configure_logger
from greetbot.types.settings import settings


async def main() -> None:
    dispatcher = Dispatcher()
    bot = Bot(token=settings.bot_token, parse_mode="HTML")

    configure_logger()
    await init_database()
    init_routers(dispatcher)

    await dispatcher.start_polling(bot)


def start() -> None:
    asyncio.run(main())


if __name__ == '__main__':
    start()
