from mako.compat import win32

from app.database.models import async_session
from app.database.models import User, UserBonusBalance, PurchaseHistory, BonusSystem, RoleHistory, Review
from sqlalchemy import select, func, distinct, update, or_
from sqlalchemy.orm import selectinload, joinedload
from datetime import datetime, timedelta


async def get_statistics(period: str = "all"):
    async with async_session() as session:
        if period == "day":
            start_date = datetime.now() - timedelta(days=1)
            period_filter = PurchaseHistory.transaction_date >= start_date
            period_label = "за последний день"
        elif period == "week":
            start_date = datetime.now() - timedelta(weeks=1)
            period_filter = PurchaseHistory.transaction_date >= start_date
            period_label = "за последнюю неделю"
        elif period == "month":
            start_date = datetime.now() - timedelta(days=30)
            period_filter = PurchaseHistory.transaction_date >= start_date
            period_label = "за последний месяц"
        else:
            period_filter = True
            period_label = "за всё время"

        # Подсчёт общего количества пользователей
        total_users_query = select(func.count(User.user_id))
        total_users = (await session.execute(total_users_query)).scalar() or 0

        # Подсчёт общей суммы покупок
        total_amount_query = select(func.sum(PurchaseHistory.amount)).where(period_filter)
        total_amount = (await session.execute(total_amount_query)).scalar() or 0.0

        # Подсчёт общей суммы выданных бонусов
        total_bonus_amount_query = select(func.sum(PurchaseHistory.bonus_amount)).where(
            PurchaseHistory.transaction_type == "Пополнение",
            period_filter
        )
        total_bonus_amount = (await session.execute(total_bonus_amount_query)).scalar() or 0.0

        # Подсчёт общего количества транзакций
        total_transactions_query = select(func.count(PurchaseHistory.id)).where(period_filter)
        total_transactions = (await session.execute(total_transactions_query)).scalar() or 0

        # Подсчёт средней суммы покупки
        average_purchase_amount_query = select(func.avg(PurchaseHistory.amount)).where(period_filter)
        average_purchase_amount = (await session.execute(average_purchase_amount_query)).scalar() or 0.0

        # Подсчёт количества активных пользователей
        active_users_query = select(func.count(distinct(PurchaseHistory.user_id))).where(period_filter)
        active_users = (await session.execute(active_users_query)).scalar() or 0

        # Подсчёт общей суммы бонусов на балансах
        total_bonus_balance_query = select(func.sum(UserBonusBalance.balance))
        total_bonus_balance = (await session.execute(total_bonus_balance_query)).scalar() or 0.0

        return {
            "total_users": total_users,
            "total_amount": total_amount,
            "total_bonus_amount": total_bonus_amount,
            "total_transactions": total_transactions,
            "average_purchase_amount": average_purchase_amount,
            "active_users": active_users,
            "total_bonus_balance": total_bonus_balance,
            "period_label": period_label,
        }


async def set_bonus_system_settings(amount: int, setting_type: str):
    async with async_session() as session:
        query = await session.execute(select(BonusSystem).where(BonusSystem.id == 1))
        bonus_settings = query.scalar()

        if not bonus_settings:
            bonus_settings = BonusSystem(cashback=5, max_debit=30, start_bonus_balance=500)
            session.add(bonus_settings)

        if setting_type == "cashback":
            bonus_settings.cashback = amount
        elif setting_type == "max_debit":
            bonus_settings.max_debit = amount
        elif setting_type == "welcome_bonus":
            bonus_settings.start_bonus_balance = amount
        else:
            raise ValueError("Некорректный тип параметра: используйте 'cashback' или 'max_debit'")

        await session.commit()


async def change_user_role(user_id, new_role) -> bool:
    async with async_session() as session:
        user_query = select(User).where(User.user_id == user_id)
        user_result = await session.execute(user_query)
        user = user_result.scalar()

        if not user:
            return False

        update_query = (
            update(User)
            .where(User.user_id == user_id)
            .values(role=new_role)
        )
        await session.execute(update_query)
        await session.commit()

        return True


async def add_role_history(admin_id, user_id, role):
    async with async_session() as session:
        new_role_entry = RoleHistory(
            admin_id=admin_id,
            user_id=user_id,
            role=role,
            assigned_date=datetime.now()
        )
        session.add(new_role_entry)
        await session.commit()


async def get_admin_and_employees_names():
    async with async_session() as session:
        admin_query = select(User.user_id, User.name).where(User.role == "Администратор")
        admin_result = await session.execute(admin_query)
        admin_dict = {row.user_id: row.name for row in admin_result}

        employee_query = select(User.user_id, User.name).where(User.role == "Работник")
        employee_result = await session.execute(employee_query)
        employee_dict = {row.user_id: row.name for row in employee_result}

        return admin_dict, employee_dict


async def get_worker_statistics(worker_id, period: str = "all"):
    async with async_session() as session:
        if period == "day":
            start_date = datetime.now() - timedelta(days=1)
            period_filter = PurchaseHistory.transaction_date >= start_date
            period_label = "за последний день"
        elif period == "week":
            start_date = datetime.now() - timedelta(weeks=1)
            period_filter = PurchaseHistory.transaction_date >= start_date
            period_label = "за последнюю неделю"
        elif period == "month":
            start_date = datetime.now() - timedelta(days=30)
            period_filter = PurchaseHistory.transaction_date >= start_date
            period_label = "за последний месяц"
        else:
            period_filter = True
            period_label = "за всё время"

        # Получаем информацию о работнике
        worker_query = select(User).where(User.user_id == worker_id)
        worker = (await session.execute(worker_query)).scalar()

        if not worker:
            return None

        # Получаем дату последней выдачи роли
        role_query = (
            select(RoleHistory.assigned_date)
            .where(RoleHistory.user_id == worker_id)
            .order_by(RoleHistory.assigned_date.desc())
            .limit(1)
        )
        role_assigned_date = (await session.execute(role_query)).scalar() or "Неизвестно"

        # Подсчёт количества транзакций
        total_transactions_query = select(func.count(PurchaseHistory.id)).where(
            PurchaseHistory.worker_id == worker_id,
            period_filter
        )
        total_transactions = (await session.execute(total_transactions_query)).scalar() or 0

        # Подсчёт общей суммы всех операций
        total_amount_query = select(func.sum(PurchaseHistory.amount)).where(
            PurchaseHistory.worker_id == worker_id,
            period_filter
        )
        total_amount = (await session.execute(total_amount_query)).scalar() or 0.0

        # Подсчёт суммы зачисления бонусов
        total_add_query = select(func.sum(PurchaseHistory.bonus_amount)).where(
            PurchaseHistory.worker_id == worker_id,
            PurchaseHistory.transaction_type == "Пополнение",
            period_filter
        )
        total_add = (await session.execute(total_add_query)).scalar() or 0.0

        # Подсчёт суммы списания бонусов
        total_remove_query = select(func.sum(PurchaseHistory.bonus_amount)).where(
            PurchaseHistory.worker_id == worker_id,
            PurchaseHistory.transaction_type == "Списание",
            period_filter
        )
        total_remove = (await session.execute(total_remove_query)).scalar() or 0.0

        # Подсчёт количества оценок
        total_ratings_query = select(func.count(Review.id)).where(Review.worker_id == worker_id)
        total_ratings = (await session.execute(total_ratings_query)).scalar() or 0

        return {
            "name": worker.name,
            "user_id": worker.user_id,
            "role_assigned_date": role_assigned_date,
            "total_transactions": total_transactions,
            "total_amount": total_amount,
            "total_add": total_add,
            "total_remove": total_remove,
            "total_ratings": total_ratings,
            "period_label": period_label,
        }


async def get_users_by_balance(balance_input):
    async with async_session() as session:
        if balance_input == 1000:
            balance_filter = UserBonusBalance.balance.between(1000, 5000)
        elif balance_input == 5000:
            balance_filter = UserBonusBalance.balance.between(5001, 10000)
        elif balance_input == 10000:
            balance_filter = UserBonusBalance.balance > 10000
        else:
            return {}

        query = select(User).join(UserBonusBalance).where(balance_filter).options(selectinload(User.bonus_balance))
        result = await session.execute(query)
        users = result.scalars().all()

        users_dict = {}
        for user in users:
            users_dict[user.user_id] = {
                'name': user.name,
                'bonus-balance': user.bonus_balance.balance
            }

        return users_dict


async def get_worker_average_rating(worker_id: str) -> float | None:
    async with async_session() as session:
        query = select(func.avg(Review.rating)).where(Review.worker_id == worker_id)
        result = await session.execute(query)
        avg_rating = result.scalar()
        return round(avg_rating, 2) if avg_rating else None


async def get_worker_reviews(worker_id: str) -> list[dict]:
    async with async_session() as session:
        start_date = datetime.now() - timedelta(days=30)
        query = (
            select(Review, User.name, PurchaseHistory.amount, PurchaseHistory.transaction_type)
            .join(User, Review.user_id == User.user_id)
            .join(PurchaseHistory, Review.purchase_id == PurchaseHistory.id)
            .where(Review.worker_id == worker_id, Review.review_date >= start_date)
            .order_by(Review.review_date.desc())
        )
        result = await session.execute(query)
        reviews = result.all()

        return [
            {
                "user_id": review.user_id,
                "name": name,
                "review_date": review.review_date,
                "amount": amount,
                "transaction_type": transaction_type,
                "rating": review.rating,
                "comment": review.comment or "Без комментария"
            }
            for review, name, amount, transaction_type in reviews
        ]


async def get_tg_id_mailing():
    async with async_session() as session:
        users = await session.scalars(
            select(User.user_id)
            .where(or_(User.role == 'Пользователь', User.role == 'Работник'))
        )
        result = users.all()

        return result


async def get_tg_id_users():
    async with async_session() as session:
        users = await session.scalars(
            select(User.user_id)
            .where(User.role == 'Пользователь')
        )
        result = users.all()

        return result