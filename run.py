import asyncio

from config import bot, dp
from app.database.models import async_main
from app.handlers.main import setup_middleware
from app.scheduler.tasks import setup_scheduler

from app.database.seed import seed


async def main():
    await async_main()
    await seed()

    routers = await setup_middleware()
    for router in routers:
        dp.include_router(router)

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