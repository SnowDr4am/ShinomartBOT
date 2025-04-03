from sqlalchemy import select, desc, func, case
from datetime import datetime, timedelta
import pytz
from app.database.models import async_session
from app.database.models import User, UserBonusBalance, PurchaseHistory, BonusSystem, Review, Appointment, Settings, QRCode
from sqlalchemy.orm import joinedload
from app.servers.config import ADMIN_ID

EKATERINBURG_TZ = pytz.timezone('Asia/Yekaterinburg')

async def set_user(user_id, date_today, name, mobile_phone, birthday, bonus_balance):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.user_id == user_id))
        if not user:
            role = 'Администратор' if str(user_id) in ADMIN_ID else 'Пользователь'

            new_user = User(
                user_id=user_id,
                registration_date=date_today,
                name=name,
                mobile_phone=mobile_phone,
                birthday_date=birthday,
                role=role
            )

            session.add(new_user)
            await session.flush()

            new_balance = UserBonusBalance(
                user_id=new_user.user_id,
                balance=bonus_balance
            )
            session.add(new_balance)

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


async def get_phone_numbers_by_suffix(suffix: str):
    async with async_session() as session:
        query = select(User.mobile_phone).where(User.mobile_phone.endswith(suffix))
        result = await session.execute(query)
        phone_numbers = result.scalars().all()
        return phone_numbers


async def get_user_by_phone(phone_number: str):
    async with async_session() as session:
        query = (
            select(User)
            .where(User.mobile_phone == phone_number)
            .options(joinedload(User.bonus_balance))
        )
        result = await session.execute(query)
        return result.scalar()


async def set_bonus_balance(user_id, action, amount_bonus, amount_cell, worker_id):
    async with async_session() as session:
        query = select(UserBonusBalance).where(UserBonusBalance.user_id == user_id)
        result = await session.execute(query)
        bonus_balance = result.scalar()

        if not bonus_balance:
            return False

        if action == 'add':
            bonus_balance.balance += amount_bonus
            transaction_type = "Пополнение"
        elif action == 'remove':
            if bonus_balance.balance < amount_bonus:
                bonus_balance.balance = 0
            else:
                bonus_balance.balance -= amount_bonus
            transaction_type = "Списание"
        else:
            return False

        new_transaction = PurchaseHistory(
            user_id = user_id,
            worker_id=worker_id,
            transaction_date = datetime.now(),
            transaction_type = transaction_type,
            amount = amount_cell,
            bonus_amount = amount_bonus
        )
        session.add(new_transaction)

        await session.commit()
        return True


async def get_bonus_system_settings():
    async with async_session() as session:
        query = select(BonusSystem.cashback, BonusSystem.max_debit)
        result = await session.execute(query)
        settings = result.first()

        if not settings:
            new_settings = BonusSystem(cashback=5, max_debit=30, start_bonus_balance=300)
            session.add(new_settings)
            await session.commit()

            result = await session.execute(query)
            settings = result.first()
        return {
            "cashback": settings.cashback,
            "max_debit": settings.max_debit,
            "start_bonus_balance": settings.start_bonus_balance
        }


async def get_monthly_report(year: int, month: int) -> dict:
    async with async_session() as session:
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        new_users_query = (
            select(func.count(User.id))
            .where(User.registration_date >= start_date)
            .where(User.registration_date < end_date)
        )
        new_users = await session.scalar(new_users_query) or 0

        transactions_query = (
            select(
                func.count(PurchaseHistory.id).label("sales_count"),
                func.sum(PurchaseHistory.amount).label("sales_amount"),
                func.sum(
                    case(
                        (PurchaseHistory.transaction_type == "Пополнение", PurchaseHistory.bonus_amount),
                        else_=0
                    )
                ).label("bonuses_added"),
                func.sum(
                    case(
                        (PurchaseHistory.transaction_type == "Списание", PurchaseHistory.bonus_amount),
                        else_=0
                    )
                ).label("bonuses_spent")
            )
            .where(PurchaseHistory.transaction_date >= start_date)
            .where(PurchaseHistory.transaction_date < end_date)
        )
        result = await session.execute(transactions_query)
        row = result.one()

        return {
            "new_users": new_users,
            "sales_count": row.sales_count or 0,
            "sales_amount": row.sales_amount or 0.0,
            "bonuses_added": row.bonuses_added or 0.0,
            "bonuses_spent": row.bonuses_spent or 0.0
        }


async def get_last_transaction(user_id: str) -> PurchaseHistory | None:
    async with async_session() as session:
        stmt = select(PurchaseHistory).where(PurchaseHistory.user_id == user_id).order_by(PurchaseHistory.transaction_date.desc()).limit(1)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def check_review_exists(purchase_id: int) -> bool:
    async with async_session() as session:
        review_exists = await session.execute(
            select(Review).where(Review.purchase_id == purchase_id)
        )
        return bool(review_exists.scalar_one_or_none())


async def save_review(
    user_id: str,
    purchase_id: int,
    worker_id: str,
    rating: int,
    comment: str | None
) -> None:
    async with async_session() as session:
        review = Review(
            user_id=user_id,
            purchase_id=purchase_id,
            worker_id=worker_id,
            review_date=datetime.now(),
            rating=rating,
            comment=comment
        )
        session.add(review)
        await session.commit()


async def get_appointments_for_today() -> list[Appointment]:
    """Возвращает все записи на текущий день, отсортированные по времени."""
    async with async_session() as session:
        today = datetime.now(EKATERINBURG_TZ).replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)

        stmt = select(Appointment).where(
            Appointment.date_time.between(today, tomorrow - timedelta(seconds=1))
        ).order_by(Appointment.date_time)
        result = await session.execute(stmt)
        return result.scalars().all()


async def get_upcoming_appointments_for_notification(current_time: datetime) -> list[Appointment]:
    """Возвращает неподтверждённые записи в диапазоне текущего времени + 3 часа, которым не отправлено уведомление."""
    async with async_session() as session:
        start_time = current_time
        end_time = current_time + timedelta(hours=3)

        stmt = select(Appointment).where(
            (Appointment.date_time.between(start_time, end_time)) &
            (Appointment.is_confirmed == False) &
            (Appointment.is_notified == False)
        ).order_by(Appointment.date_time)
        result = await session.execute(stmt)
        return result.scalars().all()


async def confirm_appointment(user_id: str) -> bool:
    """Подтверждает запись пользователя."""
    async with async_session() as session:
        stmt = select(Appointment).where(Appointment.user_id == user_id)
        result = await session.execute(stmt)
        appointment = result.scalars().first()

        if appointment:
            appointment.is_confirmed = True
            await session.commit()
            return True
        return False


async def delete_appointment(user_id: str) -> bool:
    """Удаляет запись пользователя."""
    async with async_session() as session:
        stmt = select(Appointment).where(Appointment.user_id == user_id)
        result = await session.execute(stmt)
        appointment = result.scalars().first()

        if appointment:
            await session.delete(appointment)
            await session.commit()
            return True
        return False


async def set_notified(user_id: str) -> bool:
    """Отмечает, что пользователю отправлено уведомление."""
    async with async_session() as session:
        stmt = select(Appointment).where(Appointment.user_id == user_id)
        result = await session.execute(stmt)
        appointment = result.scalars().first()

        if appointment:
            appointment.is_notified = True
            await session.commit()
            return True
        return False


async def get_daily_message_id() -> int | None:
    """Получает ID сообщения из таблицы Settings."""
    async with async_session() as session:
        stmt = select(Settings).where(Settings.id == 1)
        result = await session.execute(stmt)
        settings = result.scalars().first()
        return settings.daily_message_id if settings else None


async def set_daily_message_id(message_id: int) -> bool:
    """Обновляет или создаёт запись с ID сообщения в таблице Settings."""
    async with async_session() as session:
        try:
            stmt = select(Settings).where(Settings.id == 1)
            result = await session.execute(stmt)
            settings = result.scalars().first()

            if settings:
                settings.daily_message_id = message_id
            else:
                new_settings = Settings(id=1, daily_message_id=message_id)
                session.add(new_settings)

            await session.commit()
            return True
        except Exception as e:
            await session.rollback()
            return False

async def get_user_role(user_tg_id: int) -> str | None:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.user_id == str(user_tg_id))
        )
        user = result.scalars().first()
        return user.role if user else None

async def get_last_qr_code(user_id: int) -> QRCode | None:
    async with async_session() as session:
        result = await session.execute(
            select(QRCode).where(QRCode.user_id == user_id).order_by(QRCode.created_at.desc())
        )
        return result.scalars().first()

async def create_qr_code(user_id: int, phone_number: str) -> bool:
    async with async_session() as session:
            new_qr = QRCode(
                user_id=user_id,
                phone_number=phone_number,
                created_at=datetime.now(EKATERINBURG_TZ).astimezone(pytz.UTC)
            )
            session.add(new_qr)
            await session.commit()

async def check_qr_code(phone_number: str) -> QRCode | None:
    async with async_session() as session:
        result = await session.execute(
            select(QRCode).where(QRCode.phone_number == phone_number).order_by(QRCode.created_at.desc())
        )
        qr = result.scalars().first()
        if qr and qr.created_at:
            now_utc = datetime.now(EKATERINBURG_TZ).astimezone(pytz.UTC)
            created_at_utc = qr.created_at.replace(tzinfo=pytz.UTC) if qr.created_at.tzinfo is None else qr.created_at
            if (now_utc - created_at_utc) <= timedelta(minutes=30):
                return qr
        return None

async def get_user_by_tg_id(user_tg_id: int) -> User | None:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.user_id == str(user_tg_id))
        )
        return result.scalars().first()