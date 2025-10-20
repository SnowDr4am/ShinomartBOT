from sqlalchemy import select
from datetime import datetime
from typing import Dict, Optional

from app.database.model import AsyncSessionLocal, UserBonusBalance, BonusSystem, PurchaseHistory


class BonusService:
    # ---------- SAVE or UPDATE user bonus ----------
    @classmethod
    async def save_or_update_user_bonus(
        cls,
        *,
        user_id: str,
        action: str,               # 'add' | 'remove'
        amount_bonus: float,       # сколько бонусов прибавить/списать
        amount_cell: float,        # денежная сумма операции (для истории)
        worker_id: str,            # кто провёл операцию
        create_if_missing: bool = True,
        clamp_to_zero: bool = True,
        add_history: bool = True,
        when: Optional[datetime] = None,
    ) -> UserBonusBalance:
        """
        Изменяет баланс пользователя, создаёт запись при необходимости и, опционально,
        пишет транзакцию в PurchaseHistory.
        """
        if amount_bonus < 0:
            raise ValueError("amount_bonus не может быть отрицательным")
        if action not in {"add", "remove"}:
            raise ValueError("action должен быть 'add' или 'remove'")

        async with AsyncSessionLocal() as session:
            async with session.begin():
                # Получить/создать баланс
                result = await session.execute(
                    select(UserBonusBalance).where(UserBonusBalance.user_id == user_id)
                )
                bonus = result.scalars().first()
                if bonus is None:
                    if not create_if_missing:
                        raise ValueError("Бонусный счёт не найден")
                    bonus = UserBonusBalance(user_id=user_id, balance=0.0)
                    session.add(bonus)

                # Применить операцию
                if action == "add":
                    bonus.balance = float(bonus.balance) + float(amount_bonus)
                    tx_type = "Пополнение"
                else:  # remove
                    new_balance = float(bonus.balance) - float(amount_bonus)
                    if clamp_to_zero and new_balance < 0:
                        new_balance = 0.0
                    bonus.balance = new_balance
                    tx_type = "Списание"

                # История транзакций (как у вас было)
                if add_history:
                    session.add(
                        PurchaseHistory(
                            user_id=user_id,
                            worker_id=worker_id,
                            transaction_date=when or datetime.now(),
                            transaction_type=tx_type,
                            amount=float(amount_cell),
                            bonus_amount=float(amount_bonus),
                        )
                    )

            # за пределами транзакции можно освежить объект
            await session.refresh(bonus)
            return bonus


    # ---------- GET settings ----------
    @classmethod
    async def get_settings(cls) -> BonusSystem:
        """
        Возвращает единственную запись BonusSystem.
        Если отсутствует — создаёт с дефолтами и возвращает.
        """
        async with AsyncSessionLocal() as session:
            async with session.begin():
                res = await session.execute(select(BonusSystem).limit(1))
                settings = res.scalars().first()
                if settings is None:
                    settings = BonusSystem()  # значения по умолчанию заданы в модели
                    session.add(settings)
            await session.refresh(settings)
            return settings


    # ---------- SAVE or UPDATE settings ----------
    @classmethod
    async def save_or_update_settings(
            cls,
            *,
            cashback: Optional[int] = None,
            max_debit: Optional[int] = None,
            start_bonus_balance: Optional[int] = None,
            voting_bonus: Optional[int] = None,
            vip_cashback: Optional[int] = None,
            **extras,  # игнор/расширяемость
    ) -> BonusSystem:
        """
        Обновляет (или создаёт) настройки бонусной системы.
        Передавайте только те поля, которые хотите поменять.
        """
        allowed_fields = {
            "cashback",
            "max_debit",
            "start_bonus_balance",
            "voting_bonus",
            "vip_cashback",
        }
        unknown = set(extras.keys()) - set()
        if unknown:
            # Если вдруг прокинут лишние именованные аргументы — явно сообщим
            raise ValueError(f"Неизвестные параметры: {', '.join(sorted(unknown))}")

        async with AsyncSessionLocal() as session:
            async with session.begin():
                res = await session.execute(select(BonusSystem).limit(1))
                settings = res.scalars().first()
                if settings is None:
                    settings = BonusSystem()
                    session.add(settings)

                for name, value in {
                    "cashback": cashback,
                    "max_debit": max_debit,
                    "start_bonus_balance": start_bonus_balance,
                    "voting_bonus": voting_bonus,
                    "vip_cashback": vip_cashback,
                }.items():
                    if value is not None:
                        if not isinstance(value, int):
                            raise ValueError(f"{name} должен быть int")
                        setattr(settings, name, value)

            await session.refresh(settings)
            return settings