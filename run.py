import asyncio
from aiogram import Bot, Dispatcher

from app.servers.config import BOT_TOKEN
from app.database.models import async_main
from app.handlers.main import setup_middleware, user_router, admin_router, employee_router

from app.handlers.user import user
from app.handlers.admin import admin
from app.handlers.employee import employee

async def main():
    await async_main()
    await setup_middleware()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(user_router)
    dp.include_router(admin_router)
    dp.include_router(employee_router)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')