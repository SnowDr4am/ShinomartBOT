from aiogram import BaseMiddleware
from aiogram.types import Message
from aiogram.fsm.context import FSMContext


class CancelMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        state: FSMContext = data.get("state")

        if isinstance(event, Message) and event.text and event.text.lower() == "отмена":
            if state is not None:
                await state.clear()
                await event.answer("❌ Операция отменена")
                return

        return await handler(event, data)
