import asyncio
from collections import defaultdict

from aiogram import BaseMiddleware
from aiogram.types import Message


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