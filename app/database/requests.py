from sqlalchemy import select, func, desc, or_, and_

from app.database.models import async_session
from app.database.models import User, UserBonusBalance, PurchaseHistory


async def set_user(user_id, date_today, name, mobile_phone, birthday):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.user_id == user_id))

        if not user:
            new_user = User(
                user_id=user_id,
                registration_date=date_today,
                name=name,
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


async def check_mobile_phone(mobile_phone: str) -> bool:
    async with async_session() as session:
        return await session.scalar(select(User).where(User.mobile_phone == mobile_phone)) is not None


async def check_user_by_id(user_id) -> bool:
    async with async_session() as session:
        result = await session.scalar(select(User).where(User.user_id == user_id))
        return result is not None


async def get_user_profile(user_id) -> dict:
    async with async_session() as session:
        result = await session.execute(
            select(User)
            .where(User.user_id == user_id)
        )
        user = result.scalars().first()

        if user:
            profile_data = {
                "user_id": user.user_id,
                "name": user.name or "Не указано",
                "registration_date": user.registration_date.strftime('%d-%m-%Y'),
                "mobile_phone": user.mobile_phone or "Не указан",
                "birthday_date": user.birthday_date.strftime('%d-%m-%Y') if user.birthday_date else "Не указана",
                "bonus_balance": await get_bonus_balance(user_id)
            }
            return profile_data
        return None


async def get_bonus_balance(user_id: str) -> float:
    async with async_session() as session:
        result = await session.execute(
            select(UserBonusBalance)
            .where(UserBonusBalance.user_id == user_id)
        )
        economy = result.scalars().first()

        if economy:
            return economy.balance
        return 0.0


async def get_last_10_transactions(user_id):
    async with async_session() as session:
        query = (
            select(PurchaseHistory)
            .where(PurchaseHistory.user_id == user_id)
            .order_by(desc(PurchaseHistory.transaction_date))
            .limit(10)
        )
        result = await session.execute(query)
        return result.scalars().all()