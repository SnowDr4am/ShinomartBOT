from sqlalchemy import select, or_, and_
from sqlalchemy.orm import selectinload
from datetime import datetime
from typing import Optional, List, Iterable

from app.database.model import AsyncSessionLocal, User, RoleHistory


class UserService:
    # ---------- GET (Plural) ----------
    @classmethod
    async def get_users(
        cls,
        *,
        user_id: int | None = None,
        user_telegram_id: int | None = None,
        registration_date: datetime | None = None,
        name: str | None = None,
        mobile_phone: str | None = None,
        mobile_phone_suffix: str | None = None,
        birthday_date: datetime | None = None,
        role: str | None = None,

        with_purchase_history: bool = False,
        with_bonus_balance: bool = False,
        with_reviews: bool = False,
        with_appointments: bool = False,
        with_qr_codes: bool = False,
        with_vote_history: bool = False,
        with_vip_client: bool = False,

        limit: int | None = None,
        offset: int | None = None,
    ) -> List[User]:
        async with AsyncSessionLocal() as session:
            stmt = select(User)

            # корректные связи из текущей модели
            if with_purchase_history:
                stmt = stmt.options(selectinload(User.purchase_history))
            if with_bonus_balance:
                stmt = stmt.options(selectinload(User.bonus_balance))
            if with_reviews:
                stmt = stmt.options(selectinload(User.reviews))
            if with_appointments:
                stmt = stmt.options(selectinload(User.appointments))
            if with_qr_codes:
                stmt = stmt.options(selectinload(User.qr_codes))
            if with_vote_history:
                stmt = stmt.options(selectinload(User.vote_history))
            if with_vip_client:
                stmt = stmt.options(selectinload(User.vip_client))

            tg_str: Optional[str] = str(user_telegram_id) if user_telegram_id is not None else None
            bdate = birthday_date.date() if isinstance(birthday_date, datetime) else birthday_date

            conditions = []
            if user_id is not None:
                conditions.append(User.id == int(user_id))
            if tg_str is not None:
                conditions.append(User.user_id == tg_str)
            if registration_date is not None:
                conditions.append(User.registration_date == registration_date)
            if name is not None:
                conditions.append(User.name == name)
            if mobile_phone is not None:
                conditions.append(User.mobile_phone == mobile_phone)
            if mobile_phone_suffix:  # тот самый функционал по суффиксу
                conditions.append(User.mobile_phone.endswith(mobile_phone_suffix))
            if bdate is not None:
                conditions.append(User.birthday_date == bdate)
            if role is not None:
                conditions.append(User.role == role)

            if conditions:
                stmt = stmt.where(and_(*conditions))

            if offset is not None:
                stmt = stmt.offset(int(offset))
            if limit is not None:
                stmt = stmt.limit(int(limit))

            res = await session.execute(stmt)
            return list(res.scalars().all())


    # ---------- GET (single) ----------
    @classmethod
    async def get_user(
            cls,
            **kwargs,
    ) -> User | None:
        rows = await cls.get_users(limit=1, **kwargs)
        return rows[0] if rows else None


    # ---------- batch ----------
    @classmethod
    async def get_users_by_ids(
            cls,
            *,
            user_telegram_ids: Iterable[int],

            with_purchase_history: bool = False,
            with_bonus_balance: bool = False,
            with_reviews: bool = False,
            with_appointments: bool = False,
            with_qr_codes: bool = False,
            with_vote_history: bool = False,
            with_vip_client: bool = False,
    ) -> List[User]:
        ids = list({str(i) for i in user_telegram_ids if i is not None})
        if not ids:
            return []

        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.user_id.in_(ids))

            if with_purchase_history:
                stmt = stmt.options(selectinload(User.purchase_history))
            if with_bonus_balance:
                stmt = stmt.options(selectinload(User.bonus_balance))
            if with_reviews:
                stmt = stmt.options(selectinload(User.reviews))
            if with_appointments:
                stmt = stmt.options(selectinload(User.appointments))
            if with_qr_codes:
                stmt = stmt.options(selectinload(User.qr_codes))
            if with_vote_history:
                stmt = stmt.options(selectinload(User.vote_history))
            if with_vip_client:
                stmt = stmt.options(selectinload(User.vip_client))

            res = await session.execute(stmt)
            users = list(res.scalars().all())

            index = {uid: i for i, uid in enumerate(ids)}
            users.sort(key=lambda u: index.get(u.id, 10 ** 9))
            return users


    # ---------- SAVE OR UPDATE ----------
    @classmethod
    async def save_or_update(
            cls,
            *,
            user_id: int | None = None,
            user_telegram_id: int | None = None,
            admin_id: int | None = None,

            registration_date: datetime | None = None,
            name: str | None = None,
            mobile_phone: str | None = None,
            birthday_date: datetime | None = None,
            role: str | None = None
    ) -> User | None:
        if user_id is None and user_telegram_id is None:
            return None

        tg_str: Optional[str] = str(user_telegram_id) if user_telegram_id is not None else None
        bdate = birthday_date.date() if isinstance(birthday_date, datetime) else birthday_date

        async with AsyncSessionLocal() as session:
            conds = []
            if user_id is not None:
                conds.append(User.id == int(user_id))
            if tg_str is not None:
                conds.append(User.user_id == tg_str)

            existing = None
            if conds:
                q = select(User).where(or_(*conds))
                existing = (await session.execute(q)).scalars().first()

            patch: dict = {}
            if registration_date is not None:
                patch["registration_date"] = registration_date
            if name is not None:
                patch["name"] = name
            if mobile_phone is not None:
                patch["mobile_phone"] = mobile_phone
            if bdate is not None:
                patch["birthday_date"] = bdate
            if role is not None:
                patch["role"] = role

            if existing:
                role_changed = False
                new_role_value = patch.get("role")

                if patch:
                    old_role_value = existing.role

                    for k, v in patch.items():
                        setattr(existing, k, v)

                    if new_role_value is not None and new_role_value != old_role_value:
                        role_changed = True

                    await session.flush()

                    if role_changed:
                        session.add(
                            RoleHistory(
                                admin_id=admin_id or "system",
                                user_id=existing.user_id,
                                role=new_role_value,
                                assigned_date=datetime.utcnow(),
                            )
                        )
                await session.commit()
                return existing

            if tg_str is None:
                return None

            role_value = patch.get("role", "Пользователь")

            new_user = User(
                user_id=tg_str,
                registration_date=patch.get("registration_date", datetime.utcnow()),
                name=patch.get("name"),
                mobile_phone=patch.get("mobile_phone"),
                birthday_date=patch.get("birthday_date"),
                role=role_value,
            )
            session.add(new_user)
            await session.flush()
            await session.commit()
            return new_user