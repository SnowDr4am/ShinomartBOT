from __future__ import annotations

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy import select, delete, func, case, desc, or_, and_, distinct
from sqlalchemy.orm import selectinload

from app.database.model import (
    AsyncSessionLocal,
    PurchaseHistory,
    User,
    Review,
    RoleHistory,
    UserBonusBalance,
)


class StatisticsService:
    """Сервис для общей статистики"""
    # ---------- OVERVIEW ----------
    @classmethod
    async def get_statistics(cls, period: str = "all") -> Dict[str, Any]:
        """
        Общая статистика за период:
        period in {"day","week","month","all"}
        """
        async with AsyncSessionLocal() as session:
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
                start_date = None
                period_filter = True  # без фильтра по дате
                period_label = "за всё время"

            # Пользователи
            total_users = (await session.execute(select(func.count(User.user_id)))).scalar() or 0

            # Сумма покупок
            total_amount = (
                await session.execute(select(func.sum(PurchaseHistory.amount)).where(period_filter))
            ).scalar() or 0.0

            # Сумма выданных бонусов
            total_bonus_amount = (
                await session.execute(
                    select(func.sum(PurchaseHistory.bonus_amount)).where(
                        and_(PurchaseHistory.transaction_type == "Пополнение", period_filter)
                    )
                )
            ).scalar() or 0.0

            # Количество транзакций
            total_transactions = (
                await session.execute(select(func.count(PurchaseHistory.id)).where(period_filter))
            ).scalar() or 0

            # Средняя сумма покупки
            average_purchase_amount = (
                await session.execute(select(func.avg(PurchaseHistory.amount)).where(period_filter))
            ).scalar() or 0.0

            # Активные пользователи (совершали операции)
            active_users = (
                await session.execute(
                    select(func.count(distinct(PurchaseHistory.user_id))).where(period_filter)
                )
            ).scalar() or 0

            # Общая сумма бонусов на балансах
            total_bonus_balance = (
                await session.execute(select(func.sum(UserBonusBalance.balance)))
            ).scalar() or 0.0

            return {
                "total_users": int(total_users),
                "total_amount": float(total_amount),
                "total_bonus_amount": float(total_bonus_amount),
                "total_transactions": int(total_transactions),
                "average_purchase_amount": float(average_purchase_amount),
                "active_users": int(active_users),
                "total_bonus_balance": float(total_bonus_balance),
                "period_label": period_label,
            }

    # ---------- WORKER ----------
    @classmethod
    async def get_worker_statistics(cls, worker_id: str, period: str = "all") -> Optional[Dict[str, Any]]:
        """
        Статистика по сотруднику за период:
        - total_transactions, total_amount
        - total_add (бонусы начислены), total_remove (бонусы списаны)
        - total_ratings
        - role_assigned_date (последняя выдача роли)
        """
        async with AsyncSessionLocal() as session:
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

            # работник
            worker = (await session.execute(select(User).where(User.user_id == worker_id))).scalar()
            if not worker:
                return None

            # последняя выдача роли
            assigned = (
                await session.execute(
                    select(RoleHistory.assigned_date)
                    .where(RoleHistory.user_id == worker_id)
                    .order_by(RoleHistory.assigned_date.desc())
                    .limit(1)
                )
            ).scalar()

            # транзакции/суммы
            total_transactions = (
                await session.execute(
                    select(func.count(PurchaseHistory.id)).where(
                        and_(PurchaseHistory.worker_id == worker_id, period_filter)
                    )
                )
            ).scalar() or 0

            total_amount = (
                await session.execute(
                    select(func.sum(PurchaseHistory.amount)).where(
                        and_(PurchaseHistory.worker_id == worker_id, period_filter)
                    )
                )
            ).scalar() or 0.0

            total_add = (
                await session.execute(
                    select(func.sum(PurchaseHistory.bonus_amount)).where(
                        and_(
                            PurchaseHistory.worker_id == worker_id,
                            PurchaseHistory.transaction_type == "Пополнение",
                            period_filter,
                        )
                    )
                )
            ).scalar() or 0.0

            total_remove = (
                await session.execute(
                    select(func.sum(PurchaseHistory.bonus_amount)).where(
                        and_(
                            PurchaseHistory.worker_id == worker_id,
                            PurchaseHistory.transaction_type == "Списание",
                            period_filter,
                        )
                    )
                )
            ).scalar() or 0.0

            total_ratings = (
                await session.execute(select(func.count(Review.id)).where(Review.worker_id == worker_id))
            ).scalar() or 0

            return {
                "name": worker.name,
                "user_id": worker.user_id,
                "role_assigned_date": assigned or "Неизвестно",
                "total_transactions": int(total_transactions),
                "total_amount": float(total_amount),
                "total_add": float(total_add),
                "total_remove": float(total_remove),
                "total_ratings": int(total_ratings),
                "period_label": period_label,
            }