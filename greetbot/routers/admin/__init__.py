from aiogram import Router

from greetbot.routers.admin import main_menu, edit_greeting, add_greeting
from greetbot.services.middlewares.user import UserDBMiddleware

router = Router(name="Admin")
router.message.middleware(UserDBMiddleware(check_admin=True))
router.callback_query.middleware(UserDBMiddleware(check_admin=True))

router.include_router(main_menu.router)
router.include_router(edit_greeting.router)
router.include_router(add_greeting.router)