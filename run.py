import asyncio
from aiogram import Bot, Dispatcher

from app.servers.config import BOT_TOKEN
from app.database.models import async_main
from app.handlers.main import setup_middleware, user_router, admin_router, employee_router, ai_router
from app.scheduler.tasks import setup_scheduler

from app.handlers.user import user, registration, employee_assessment, ai_support, sched_handlers
from app.handlers.admin import admin, bonus_system, personal
from app.handlers.employee import employee, delete_appointment

async def main():
    await async_main()
    await setup_middleware()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(user_router)
    dp.include_router(admin_router)
    dp.include_router(employee_router)
    dp.include_router(ai_router)

    scheduler = await setup_scheduler(bot)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        scheduler.shutdown()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот остановлен пользователем')
    except Exception as e:
        print(f'Произошла ошибка: {e}')