from aiogram import Router
from app.middlewares.middleware import AdminMiddleware, EmployeeMiddleware, CancelMiddleware


user_router = Router(name='user_router')
admin_router = Router(name='admin_router')
employee_router = Router(name='employee_router')
ai_router = Router(name='ai_router')

async def setup_middleware():
    admin_router.message.middleware(AdminMiddleware())
    admin_router.callback_query.middleware(AdminMiddleware())
    admin_router.message.middleware(CancelMiddleware())
    admin_router.callback_query.middleware(CancelMiddleware())

    employee_router.message.middleware(EmployeeMiddleware())
    employee_router.callback_query.middleware(EmployeeMiddleware())
    employee_router.message.middleware(CancelMiddleware())
    employee_router.callback_query.middleware(CancelMiddleware())

    user_router.message.middleware(CancelMiddleware())
    user_router.callback_query.middleware(CancelMiddleware())


__all__ = ['user_router', 'admin_router', 'employee_router', 'ai_router', 'setup_middleware']