from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from greetbot.types.admin import AdminUser
from greetbot.types.settings import settings
from greetbot.types.user import ChannelUser


async def init_database():
    models = [
        ChannelUser,
        AdminUser
    ]
    db_client = AsyncIOMotorClient(settings.mongo_url)
    database = db_client.get_database(settings.mongo_db_name)
    await init_beanie(database=database, document_models=models)
