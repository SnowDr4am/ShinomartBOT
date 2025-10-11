import asyncio
from sqlalchemy import select
from collections import defaultdict
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.database.models import async_session
from app.database.models import User


class AdminMiddleware(BaseMiddleware):
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

            if role != "Администратор":
                await event.answer("❌ У вас нет доступа к этой команде")
                return

        return await handler(event, data)


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


class CancelMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        state: FSMContext = data.get("state")

        if isinstance(event, Message) and event.text and event.text.lower() == "отмена":
            if state is not None:
                await state.clear()
                await event.answer("❌ Операция отменена")
                return

        return await handler(event, data)


class MediaGroupMiddleware(BaseMiddleware):
    def __init__(self):
        self._album_data = defaultdict(list)

    async def __call__(self, handler, event: Message, data):
        if event.media_group_id:
            self._album_data[event.media_group_id].append(event)
            await asyncio.sleep(0.4)

            if len(self._album_data[event.media_group_id]) > 1:
                album = self._album_data.pop(event.media_group_id)
                data["album"] = album
                await handler(album[-1], data)
            return
        await handler(event, data)