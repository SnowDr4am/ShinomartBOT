from aiogram import F, Bot
from aiogram.types import CallbackQuery
from app.handlers.main import ai_router
import app.database.requests as rq
from app.servers.config import CHANNEL_ID_DAILY
from datetime import datetime
import pytz

EKATERINBURG_TZ = pytz.timezone('Asia/Yekaterinburg')

@ai_router.callback_query(F.data.startswith("approved:"))
async def process_appointment_response(callback: CallbackQuery, bot: Bot):
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Ошибка обработки запроса.")
        return

    _, user_id, action = parts

    if action == "yes":
        if await rq.confirm_appointment(user_id):
            await callback.message.edit_text(
                "✅ <b>Спасибо!</b> Ваша запись успешно подтверждена. 🎉\n\n"
                "⏰ <b>Мы ждём вас в назначенное время!</b>",
                parse_mode='HTML',
                reply_markup=None
            )
        else:
            await callback.message.edit_text(
                "⚠️ <b>Ошибка:</b> Запись не найдена. 😕\n\n"
                "ℹ️ <b>Проверьте статус записи или обратитесь в поддержку.</b>",
                parse_mode='HTML',
                reply_markup=None
            )

    elif action == "remove":
        if await rq.delete_appointment(user_id):
            await callback.message.edit_text(
                "❌ <b>Запись отменена.</b>\n\n"
                "ℹ️ <b>Вы можете записаться заново через меню.</b>",
                parse_mode='HTML',
                reply_markup=None
            )
        else:
            await callback.message.edit_text(
                "⚠️ <b>Ошибка:</b> Запись не найдена. 😕\n\n"
                "ℹ️ <b>Возможно, запись уже была отменена.</b>",
                parse_mode='HTML',
                reply_markup=None
            )

    else:
        await callback.answer(
            "⚠️ Неизвестное действие 🤔\n\nПожалуйста, выберите корректное действие",
            show_alert=True
        )
        return

    try:
        await update_channel_message(bot)
    except Exception as e:
        await callback.message.edit_text(
            f"{callback.message.text}\n\n⚠️ <b>Не удалось обновить отчёт в канале:</b> {str(e)}",
            parse_mode="HTML",
            reply_markup=None
        )

    await callback.answer()


async def update_channel_message(bot: Bot):
    """Обновляет сообщение в канале с актуальными записями на сегодня."""
    today = datetime.now(EKATERINBURG_TZ)

    appointments = await rq.get_appointments_for_today()

    if not appointments:
        message = (
            f"📅 <b>Запись в сервис на {today.strftime('%d.%m.%Y')} (сегодняшний день)</b>\n\n"
            "На сегодняшний день пока нет записей"
        )
    else:
        message_lines = [f"📅 <b>Запись в сервис на {today.strftime('%d.%m.%Y')} (сегодняшний день)</b>\n"]
        for appt in appointments:
            user = await rq.get_user_profile(appt.user_id)
            name = user.get('name', 'Не указано') if user else 'Не указано'
            status = "✅ Подтверждена" if appt.is_confirmed else "❌ Не подтверждена"
            message_lines.append(
                "—————————\n"
                f"<b>Имя клиента:</b> {name}\n"
                f"<b>Номер телефона:</b> <code>{appt.mobile_phone}</code>\n"
                f"<b>Время записи:</b> {appt.date_time.strftime('%H:%M')}\n"
                f"<b>Статус:</b> {status}\n"
            )
        message = "\n".join(message_lines) + "—————————"

    daily_message_id = await rq.get_daily_message_id()

    if daily_message_id:
        try:
            if len(message) > 4096:
                message = message[:4090] + "\n...\n(Сообщение обрезано из-за лимита Telegram)"
            await bot.edit_message_text(
                chat_id=CHANNEL_ID_DAILY,
                message_id=daily_message_id,
                text=message,
                parse_mode="HTML"
            )
        except Exception as e:
            raise
    else:
        try:
            msg = await bot.send_message(
                chat_id=CHANNEL_ID_DAILY,
                text=message,
                parse_mode="HTML"
            )
            await rq.set_daily_message_id(msg.message_id)
        except Exception as e:
            raise