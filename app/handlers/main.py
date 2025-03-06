from aiogram import Router
from app.middlewares.middleware import AdminMiddleware, EmployeeMiddleware


user_router = Router(name='user_router')
admin_router = Router(name='admin_router')
employee_router = Router(name='employee_router')

async def setup_middleware():
    admin_router.message.middleware(AdminMiddleware())
    employee_router.message.middleware(EmployeeMiddleware())

__all__ = ['user_router', 'admin_router', 'employee_router', 'setup_middleware']