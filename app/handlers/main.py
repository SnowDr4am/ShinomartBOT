from aiogram import Router
from app.middlewares.middleware import AdminMiddleware, EmployeeMiddleware
import app.database.requests as rq


user_router = Router(name='user_router')
admin_router = Router(name='admin_router')
employee_router = Router(name='employee_router')

async def setup_middleware():
    admin_list, employee_list = await rq.get_admin_and_employee_ids()

    admin_router.message.middleware(AdminMiddleware(admin_list))
    employee_router.message.middleware(EmployeeMiddleware(employee_list))

__all__ = ['user_router', 'admin_router', 'employee_router', 'setup_middleware']