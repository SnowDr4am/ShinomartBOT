from sqlalchemy import select, func, desc, or_, and_

from app.database.models import async_session
from app.database.models import User


async def set_user(user_id, date_today, mobile_phone, birthday):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.user_id == user_id))

        if not user:
            new_user = User(
                user_id=user_id,
                registration_date=date_today,
                mobile_phone=mobile_phone,
                birthday_date=birthday,
                role='Пользователь'
            )

            session.add(new_user)
            await session.commit()

            return True
        return False


async def get_admin_and_employee_ids():
    async with async_session() as session:
        admin_query = select(User.user_id).where(User.role == "Администратор")
        admin_result = await session.execute(admin_query)
        admin_ids = [row.user_id for row in admin_result]

        employee_query = select(User.user_id).where(User.role == "Работник")
        employee_result = await session.execute(employee_query)
        employee_ids = [row.user_id for row in employee_result]

        return admin_ids, employee_ids