import asyncio

from config import bot, dp
from app.handlers.main import setup_routers
from app.scheduler.tasks import setup_scheduler

from app.handlers import *


async def main():
    routers = await setup_routers()

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