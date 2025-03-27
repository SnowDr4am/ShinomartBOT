import logging
from aiogram import F, Bot
from aiogram.types import CallbackQuery
from app.handlers.main import ai_router
import app.database.requests as rq
from app.servers.config import CHANNEL_ID_DAILY
from datetime import datetime
import pytz

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),  # Логи будут записываться в файл bot.log
        logging.StreamHandler()          # И выводиться в консоль
    ]
)
logger = logging.getLogger(__name__)
EKATERINBURG_TZ = pytz.timezone('Asia/Yekaterinburg')

@ai_router.callback_query(F.data.startswith("approved:"))
async def process_appointment_response(callback: CallbackQuery, bot: Bot):
    logger.info(f"Обработка callback-запроса: {callback.data}")
    parts = callback.data.split(":")
    if len(parts) != 3:
        logger.warning("Некорректный формат callback.data")
        await callback.answer("Ошибка обработки запроса.")
        return

    _, user_id, action = parts
    logger.info(f"User_id: {user_id}, Action: {action}")

    if action == "yes":
        logger.info(f"Подтверждение записи для user_id: {user_id}")
        if await rq.confirm_appointment(user_id):
            await callback.message.edit_text(
                "✅ <b>Спасибо!</b> Ваша запись успешно подтверждена. 🎉\n\n"
                "⏰ <b>Мы ждём вас в назначенное время!</b>",
                parse_mode='HTML',
                reply_markup=None
            )
            logger.info(f"Запись для user_id: {user_id} успешно подтверждена")
        else:
            await callback.message.edit_text(
                "⚠️ <b>Ошибка:</b> Запись не найдена. 😕\n\n"
                "ℹ️ <b>Проверьте статус записи или обратитесь в поддержку.</b>",
                parse_mode='HTML',
                reply_markup=None
            )
            logger.warning(f"Запись для user_id: {user_id} не найдена при подтверждении")

    elif action == "remove":
        logger.info(f"Удаление записи для user_id: {user_id}")
        if await rq.delete_appointment(user_id):
            await callback.message.edit_text(
                "❌ <b>Запись отменена.</b>\n\n"
                "ℹ️ <b>Вы можете записаться заново через меню.</b>",
                parse_mode='HTML',
                reply_markup=None
            )
            logger.info(f"Запись для user_id: {user_id} успешно удалена")
        else:
            await callback.message.edit_text(
                "⚠️ <b>Ошибка:</b> Запись не найдена. 😕\n\n"
                "ℹ️ <b>Возможно, запись уже была отменена.</b>",
                parse_mode='HTML',
                reply_markup=None
            )
            logger.warning(f"Запись для user_id: {user_id} не найдена при удалении")

    else:
        logger.warning(f"Неизвестное действие: {action}")
        await callback.answer(
            "⚠️ Неизвестное действие 🤔\n\nПожалуйста, выберите корректное действие",
            show_alert=True
        )
        return

    # Обновление сообщения в канале
    logger.info("Попытка обновления сообщения в канале")
    try:
        await update_channel_message(bot)
        logger.info("Сообщение в канале успешно обновлено")
    except Exception as e:
        logger.error(f"Ошибка при обновлении сообщения в канале: {e}")
        await callback.message.edit_text(
            f"{callback.message.text}\n\n⚠️ <b>Не удалось обновить отчёт в канале:</b> {str(e)}",
            parse_mode="HTML",
            reply_markup=None
        )

    await callback.answer()


async def update_channel_message(bot: Bot):
    """Обновляет сообщение в канале с актуальными записями на сегодня."""
    logger.info("Начало обновления сообщения в канале")
    today = datetime.now(EKATERINBURG_TZ)
    logger.info(f"Сегодняшняя дата: {today.strftime('%d.%m.%Y')}")

    appointments = await rq.get_appointments_for_today()
    logger.info(f"Количество записей на сегодня: {len(appointments)}")

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

    logger.info(f"Длина сформированного сообщения: {len(message)} символов")
    daily_message_id = await rq.get_daily_message_id()
    logger.info(f"Получен daily_message_id: {daily_message_id}")

    if daily_message_id:
        try:
            if len(message) > 4096:
                logger.warning("Сообщение превышает лимит Telegram (4096 символов), обрезаем")
                message = message[:4090] + "\n...\n(Сообщение обрезано из-за лимита Telegram)"
            logger.info(f"Попытка редактирования сообщения с ID {daily_message_id} в канале {CHANNEL_ID_DAILY}")
            await bot.edit_message_text(
                chat_id=CHANNEL_ID_DAILY,
                message_id=daily_message_id,
                text=message,
                parse_mode="HTML"
            )
            logger.info("Сообщение в канале успешно отредактировано")
        except Exception as e:
            logger.error(f"Ошибка при редактировании сообщения в канале: {e}")
            raise
    else:
        logger.warning("daily_message_id не найден, отправляем новое сообщение")
        try:
            msg = await bot.send_message(
                chat_id=CHANNEL_ID_DAILY,
                text=message,
                parse_mode="HTML"
            )
            await rq.set_daily_message_id(msg.message_id)
            logger.info(f"Новое сообщение отправлено, ID сохранён: {msg.message_id}")
        except Exception as e:
            logger.error(f"Ошибка при отправке нового сообщения: {e}")
            raise