from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable


class AdminMiddleware(BaseMiddleware):
    def __init__(self, admin_list: list[str]) -> None:
        self.admin_list = admin_list

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        if event.from_user.id not in self.admin_list:
            await event.answer("У вас нет доступа к этой команде")
            return

        return await handler(event, data)


class EmployeeMiddleware(BaseMiddleware):
    def __init__(self, employee_list: list[str]) -> None:
        self.employee_list = employee_list

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        if str(event.from_user.id) not in self.employee_list:
            await event.answer("У вас нет доступа к этой команде")
            return

        return await handler(event, data)