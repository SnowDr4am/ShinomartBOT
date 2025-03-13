from app.database.models import async_session
from app.database.models import User, UserBonusBalance, PurchaseHistory, BonusSystem, RoleHistory
from sqlalchemy import select, func, distinct, update
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
            bonus_settings = BonusSystem(cashback=5, max_debit=30)
            session.add(bonus_settings)

        if setting_type == "cashback":
            bonus_settings.cashback = amount
        elif setting_type == "max_debit":
            bonus_settings.max_debit = amount
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
            return None  # Если работник не найден, возвращаем None

        # Получаем дату последней выдачи роли
        role_query = (
            select(RoleHistory.assigned_date)
            .where(RoleHistory.user_id == worker_id)
            .order_by(RoleHistory.assigned_date.desc())
            .limit(1)
        )
        role_assigned_date = (await session.execute(role_query)).scalar() or "Неизвестно"

        # Подсчёт количества транзакций, совершённых работником
        total_transactions_query = select(func.count(PurchaseHistory.id)).where(
            PurchaseHistory.worker_id == worker_id,
            period_filter
        )
        total_transactions = (await session.execute(total_transactions_query)).scalar() or 0

        # Подсчёт общей суммы всех операций (Пополнения + Списания)
        total_amount_query = select(func.sum(PurchaseHistory.amount)).where(
            PurchaseHistory.worker_id == worker_id,
            period_filter
        )
        total_amount = (await session.execute(total_amount_query)).scalar() or 0.0

        # Подсчёт суммы пополнений
        total_add_query = select(func.sum(PurchaseHistory.amount)).where(
            PurchaseHistory.worker_id == worker_id,
            PurchaseHistory.transaction_type == "Пополнение",
            period_filter
        )
        total_add = (await session.execute(total_add_query)).scalar() or 0.0

        # Подсчёт суммы списаний
        total_remove_query = select(func.sum(PurchaseHistory.amount)).where(
            PurchaseHistory.worker_id == worker_id,
            PurchaseHistory.transaction_type == "Списание",
            period_filter
        )
        total_remove = (await session.execute(total_remove_query)).scalar() or 0.0

        return {
            "name": worker.name,
            "user_id": worker.user_id,
            "role_assigned_date": role_assigned_date,
            "total_transactions": total_transactions,
            "total_amount": total_amount,
            "total_add": total_add,
            "total_remove": total_remove,
            "period_label": period_label,
        }


async def get_users_with_bonus(balance):
    async with async_session() as session:
