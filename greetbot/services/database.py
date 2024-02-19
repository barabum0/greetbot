from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from greetbot.types.bot_config import Greeting
from greetbot.types.settings import settings
from greetbot.types.user import User


async def init_database():
    models = [
        User,
        Greeting
    ]
    db_client = AsyncIOMotorClient(settings.mongo_url)
    database = db_client.get_database(settings.mongo_db_name)
    await init_beanie(database=database, document_models=models)
