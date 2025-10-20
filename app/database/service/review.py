from __future__ import annotations

from typing import Optional, List
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database.model import AsyncSessionLocal, Review


class ReviewService:
    # ---------- GET (Plural) ----------
    @classmethod
    async def get_reviews(
        cls,
        *,
        review_id: Optional[int] = None,
        user_id: Optional[str] = None,
        worker_id: Optional[str] = None,
        purchase_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        min_rating: Optional[int] = None,
        with_user: bool = True,
        with_purchase: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        newest_first: bool = True,
    ) -> List[Review]:
        """
        Возвращает список отзывов с фильтрами.
        """
        async with AsyncSessionLocal() as session:
            stmt = select(Review)

            if with_user:
                stmt = stmt.options(selectinload(Review.user))
            if with_purchase:
                stmt = stmt.options(selectinload(Review.purchase))

            if review_id is not None:
                stmt = stmt.where(Review.id == review_id)
            if user_id is not None:
                stmt = stmt.where(Review.user_id == user_id)
            if worker_id is not None:
                stmt = stmt.where(Review.worker_id == worker_id)
            if purchase_id is not None:
                stmt = stmt.where(Review.purchase_id == purchase_id)
            if date_from is not None:
                stmt = stmt.where(Review.review_date >= date_from)
            if date_to is not None:
                stmt = stmt.where(Review.review_date <= date_to)
            if min_rating is not None:
                stmt = stmt.where(Review.rating >= min_rating)

            if newest_first:
                stmt = stmt.order_by(Review.review_date.desc())

            if offset is not None:
                stmt = stmt.offset(offset)
            if limit is not None:
                stmt = stmt.limit(limit)

            res = await session.execute(stmt)
            return list(res.scalars().all())


    # ---------- GET (single) ----------
    @classmethod
    async def get_review(cls, **kwargs) -> Optional[Review]:
        """
        Возвращает один отзыв по тем же параметрам, что и get_reviews (limit=1).
        Удобно для проверки существования отзыва по purchase_id.
        """
        rows = await cls.get_reviews(limit=1, **kwargs)
        return rows[0] if rows else None


    # ---------- SAVE or UPDATE ----------
    @classmethod
    async def save_or_update(
        cls,
        *,
        # способы адресации
        review_id: Optional[int] = None,
        update_by_purchase: bool = False,  # если True и указан purchase_id — обновим отзыв по покупке
        # данные отзыва
        user_id: Optional[str] = None,
        purchase_id: Optional[int] = None,
        worker_id: Optional[str] = None,
        rating: Optional[int] = None,
        comment: Optional[str] = None,
        review_date: Optional[datetime] = None,
    ) -> Review:
        """
        Создаёт новый или обновляет существующий отзыв.

        Варианты:
        - Если передан review_id — обновляет найденный отзыв.
        - Иначе, если update_by_purchase=True и задан purchase_id — обновляет отзыв по покупке,
          при отсутствии создаёт новый (если хватает данных).
        - Иначе создаёт новый (user_id, purchase_id, worker_id, rating — обязательны).

        Возвращает актуальный объект Review.
        """
        if rating is not None and not (1 <= int(rating) <= 5):
            raise ValueError("rating должен быть в диапазоне 1..5")

        async with AsyncSessionLocal() as session:
            async with session.begin():
                instance: Optional[Review] = None

                # 1) По review_id
                if review_id is not None:
                    res = await session.execute(select(Review).where(Review.id == review_id))
                    instance = res.scalars().first()
                    if instance is None:
                        raise ValueError("Review с таким id не найден")

                # 2) По purchase_id (upsert по покупке)
                elif update_by_purchase and purchase_id is not None:
                    res = await session.execute(
                        select(Review).where(Review.purchase_id == purchase_id)
                    )
                    instance = res.scalars().first()

                # Создание
                if instance is None:
                    # при создании требуемые поля
                    required_missing = []
                    if user_id is None:
                        required_missing.append("user_id")
                    if purchase_id is None:
                        required_missing.append("purchase_id")
                    if worker_id is None:
                        required_missing.append("worker_id")
                    if rating is None:
                        required_missing.append("rating")
                    if required_missing:
                        raise ValueError(
                            "Для создания Review нужны: " + ", ".join(required_missing)
                        )

                    instance = Review(
                        user_id=user_id,                 # type: ignore[arg-type]
                        purchase_id=purchase_id,        # type: ignore[arg-type]
                        worker_id=worker_id,            # type: ignore[arg-type]
                        rating=int(rating),             # type: ignore[arg-type]
                        comment=comment,
                        review_date=review_date or datetime.now(),
                    )
                    session.add(instance)

                # Обновление
                else:
                    if user_id is not None:
                        instance.user_id = user_id
                    if purchase_id is not None:
                        instance.purchase_id = purchase_id
                    if worker_id is not None:
                        instance.worker_id = worker_id
                    if rating is not None:
                        instance.rating = int(rating)
                    if comment is not None:
                        instance.comment = comment
                    if review_date is not None:
                        instance.review_date = review_date

            # вернуть актуальное состояние
            await session.refresh(instance)
            return instance