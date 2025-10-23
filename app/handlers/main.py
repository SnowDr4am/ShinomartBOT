from aiogram import Router
from app.middlewares.middleware import AdminMiddleware, EmployeeMiddleware, CancelMiddleware, MediaGroupMiddleware


priority_router = Router(name='priority_router')
media_router = Router(name="media_router")

user_router = Router(name='user_router')
admin_router = Router(name='admin_router')
employee_router = Router(name='employee_router')


async def setup_mw_to_routers(routers: list[Router]):
    for router in routers:
        router.message.middleware(CancelMiddleware())


async def setup_custom_middleware():
    admin_router.message.middleware(AdminMiddleware())
    admin_router.callback_query.middleware(AdminMiddleware())

    employee_router.message.middleware(EmployeeMiddleware())
    employee_router.callback_query.middleware(EmployeeMiddleware())

    media_router.message.middleware(MediaGroupMiddleware())
    media_router.callback_query.middleware(MediaGroupMiddleware())


async def setup_middleware():
    all_routers = [
        priority_router, media_router, user_router, admin_router, employee_router
    ]

    await setup_custom_middleware()
    await setup_mw_to_routers(all_routers)

    return all_routers