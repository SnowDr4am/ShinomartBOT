from sqlalchemy import select
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message

from app.database.models import async_session
from app.database.models import User


class EmployeeMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        async with async_session() as session:
            query = select(User.role).where(User.user_id == str(event.from_user.id))
            result = await session.execute(query)
            role = result.scalar()

            if role not in ["Работник", "Администратор"]:
                await event.answer("❌ У вас нет доступа к этой команде")
                return

        return await handler(event, data)
