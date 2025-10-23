from datetime import datetime
from zoneinfo import ZoneInfo
from aiogram import Bot
from aiogram.fsm.context import FSMContext


async def delete_message_in_state(bot: Bot, state: FSMContext, chat_id: int, only_media: bool = False):
    data = await state.get_data()
    media_message_ids = data.get("media_message_ids", [])
    action_message_ids = data.get("action_message_ids", [])

    try:
        for msg_id in media_message_ids:
            try:
                await bot.delete_message(message_id=msg_id, chat_id=chat_id)
            except Exception as e:
                continue
        if not only_media:
            for msg_id in action_message_ids:
                try:
                    await bot.delete_message(chat_id=chat_id, message_id=msg_id)
                except Exception as e:
                    continue

        data.pop("media_message_ids", None)
        data.pop("action_message_ids", None)
        await state.set_data(data)
    except Exception:
        pass


async def update_message_ids_in_state(state: FSMContext, type_message: str, msg_id: int):
    data = await state.get_data()

    if type_message == "media_message_ids":
        media_message_ids = data.get("media_message_ids") or []
        media_message_ids.append(msg_id)
        await state.update_data(media_message_ids=media_message_ids)

    elif type_message == "action_message_ids":
        action_message_ids = data.get("action_message_ids") or []
        action_message_ids.append(msg_id)
        await state.update_data(action_message_ids=action_message_ids)