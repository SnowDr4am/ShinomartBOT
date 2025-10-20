from __future__ import annotations

from typing import Optional, List, Dict, Any
from datetime import datetime

from sqlalchemy import select, delete, func, case, and_
from sqlalchemy.orm import selectinload

from app.database.model import AsyncSessionLocal, PurchaseHistory, User


class TransactionService:
    """Сервис для работы с транзакциями"""

    # ---------- GET (Plural) ----------
    @classmethod
    async def get_transactions(
        cls,
        *,
        purchase_id: Optional[int] = None,
        user_id: Optional[str] = None,
        worker_id: Optional[str] = None,
        transaction_type: Optional[str] = None,  # "Пополнение" | "Списание" | др.
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        with_user: bool = False,
        newest_first: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[PurchaseHistory]:
        async with AsyncSessionLocal() as session:
            stmt = select(PurchaseHistory)
            if with_user:
                stmt = stmt.options(selectinload(PurchaseHistory.user))

            if purchase_id is not None:
                stmt = stmt.where(PurchaseHistory.id == purchase_id)
            if user_id is not None:
                stmt = stmt.where(PurchaseHistory.user_id == user_id)
            if worker_id is not None:
                stmt = stmt.where(PurchaseHistory.worker_id == worker_id)
            if transaction_type is not None:
                stmt = stmt.where(PurchaseHistory.transaction_type == transaction_type)
            if date_from is not None:
                stmt = stmt.where(PurchaseHistory.transaction_date >= date_from)
            if date_to is not None:
                stmt = stmt.where(PurchaseHistory.transaction_date <= date_to)

            stmt = stmt.order_by(PurchaseHistory.transaction_date.desc() if newest_first else PurchaseHistory.transaction_date.asc())

            if offset is not None:
                stmt = stmt.offset(offset)
            if limit is not None:
                stmt = stmt.limit(limit)

            res = await session.execute(stmt)
            return list(res.scalars().all())

    # Удобный хелпер: последние N транзакций пользователя (по возрастанию времени)
    @classmethod
    async def get_last_transactions(
        cls, *, user_id: str, limit: int = 10
    ) -> List[PurchaseHistory]:
        rows = await cls.get_transactions(user_id=user_id, limit=limit, newest_first=True)
        return list(reversed(rows))

    # ---------- GET (single) ----------
    @classmethod
    async def get_transaction(cls, **kwargs) -> Optional[PurchaseHistory]:
        rows = await cls.get_transactions(limit=1, **kwargs)
        return rows[0] if rows else None

    # ---------- SAVE or UPDATE ----------
    @classmethod
    async def save_or_update(
        cls,
        *,
        # адресация при UPDATE
        purchase_id: Optional[int] = None,
        # данные
        user_id: Optional[str] = None,
        worker_id: Optional[str] = None,
        transaction_date: Optional[datetime] = None,
        transaction_type: Optional[str] = None,  # "Пополнение" | "Списание"
        amount: Optional[float] = None,
        bonus_amount: Optional[float] = None,
    ) -> PurchaseHistory:
        """
        Если передан purchase_id — обновляет запись, иначе создаёт новую.
        Для создания обязательны: user_id, worker_id, transaction_type, amount.
        """
        async with AsyncSessionLocal() as session:
            async with session.begin():
                instance: Optional[PurchaseHistory] = None

                if purchase_id is not None:
                    res = await session.execute(
                        select(PurchaseHistory).where(PurchaseHistory.id == purchase_id)
                    )
                    instance = res.scalars().first()
                    if instance is None:
                        raise ValueError("PurchaseHistory с таким id не найден")

                if instance is None:
                    missing = []
                    if user_id is None:
                        missing.append("user_id")
                    if worker_id is None:
                        missing.append("worker_id")
                    if transaction_type is None:
                        missing.append("transaction_type")
                    if amount is None:
                        missing.append("amount")
                    if missing:
                        raise ValueError("Для создания транзакции требуются: " + ", ".join(missing))

                    instance = PurchaseHistory(
                        user_id=user_id,
                        worker_id=worker_id,
                        transaction_date=transaction_date or datetime.now(),
                        transaction_type=transaction_type,
                        amount=float(amount),
                        bonus_amount=float(bonus_amount or 0.0),
                    )
                    session.add(instance)
                else:
                    if user_id is not None:
                        instance.user_id = user_id
                    if worker_id is not None:
                        instance.worker_id = worker_id
                    if transaction_date is not None:
                        instance.transaction_date = transaction_date
                    if transaction_type is not None:
                        instance.transaction_type = transaction_type
                    if amount is not None:
                        instance.amount = float(amount)
                    if bonus_amount is not None:
                        instance.bonus_amount = float(bonus_amount)

            await session.refresh(instance)
            return instance

    # ---------- DELETE ----------
    @classmethod
    async def delete(cls, purchase_id: int) -> bool:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                res = await session.execute(
                    delete(PurchaseHistory).where(PurchaseHistory.id == purchase_id)
                )
                affected = getattr(res, "rowcount", None)
            return bool(affected and affected > 0)

    # ---------- REPORTS ----------
    @classmethod
    async def get_monthly_report(cls, *, year: int, month: int) -> Dict[str, Any]:
        """
        Месячный отчёт:
        - new_users: количество новых пользователей
        - sales_count: число операций
        - sales_amount: сумма по amount
        - bonuses_added: сумма бонусов по операциям 'Пополнение'
        - bonuses_spent: сумма бонусов по операциям 'Списание'
        """
        async with AsyncSessionLocal() as session:
            start_date = datetime(year, month, 1)
            end_date = datetime(year + (1 if month == 12 else 0), (1 if month == 12 else month + 1), 1)

            # Новые пользователи
            new_users_query = (
                select(func.count(User.id))
                .where(User.registration_date >= start_date)
                .where(User.registration_date < end_date)
            )
            new_users = (await session.execute(new_users_query)).scalar() or 0

            # Агрегации по транзакциям
            q = (
                select(
                    func.count(PurchaseHistory.id).label("sales_count"),
                    func.sum(PurchaseHistory.amount).label("sales_amount"),
                    func.sum(
                        case(
                            (PurchaseHistory.transaction_type == "Пополнение", PurchaseHistory.bonus_amount),
                            else_=0,
                        )
                    ).label("bonuses_added"),
                    func.sum(
                        case(
                            (PurchaseHistory.transaction_type == "Списание", PurchaseHistory.bonus_amount),
                            else_=0,
                        )
                    ).label("bonuses_spent"),
                )
                .where(and_(PurchaseHistory.transaction_date >= start_date, PurchaseHistory.transaction_date < end_date))
            )
            row = (await session.execute(q)).one()

            return {
                "new_users": new_users,
                "sales_count": row.sales_count or 0,
                "sales_amount": float(row.sales_amount or 0.0),
                "bonuses_added": float(row.bonuses_added or 0.0),
                "bonuses_spent": float(row.bonuses_spent or 0.0),
            }
