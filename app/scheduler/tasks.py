from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
import pytz
import app.database.requests as rq
import app.keyboards.user.user as kb
from app.servers.config import CHANNEL_ID_DAILY
from datetime import datetime

EKATERINBURG_TZ = pytz.timezone('Asia/Yekaterinburg')

async def send_monthly_report(bot: Bot):
    now = datetime.now(EKATERINBURG_TZ)
    year, month = now.year, now.month
    report_data = await rq.get_monthly_report(year, month)
    month_names = {1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель", 5: "Май", 6: "Июнь",
                   7: "Июль", 8: "Август", 9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"}
    report = (
        f"📅 <b>Отчёт за {month_names[month]} {year} года</b>\n\n"
        f"👥 <b>Новых пользователей:</b> {report_data['new_users']}\n"
        f"🛒 <b>Количество продаж:</b> {report_data['sales_count']}\n"
        f"💸 <b>Сумма всех транзакций:</b> {report_data['sales_amount']:.2f} руб.\n"
        f"🎁 <b>Начислено бонусов:</b> {report_data['bonuses_added']:.2f}\n"
        f"🔥 <b>Списано бонусов:</b> {report_data['bonuses_spent']:.2f}\n\n"
        f"✨ <i>Отчёт сформирован {now.strftime('%d.%m.%Y в %H:%M')}</i>\n"
    )
    try:
        await bot.send_message(chat_id=CHANNEL_ID_DAILY, text=report, parse_mode="HTML")
        print("Ежемесячный отчёт отправлен")
    except Exception as e:
        print(f"Ошибка отправки отчёта: {e}")

async def send_daily_appointments(bot: Bot) -> int | None:
    """Отправляет список записей на текущий день в Telegram-канал в 8:00."""
    today = datetime.now(EKATERINBURG_TZ)
    appointments = await rq.get_appointments_for_today()
    if not appointments:
        message = f"📅 <b>Запись в сервис на {today.strftime('%d.%m.%Y')} (сегодняшний день)</b>\n\nНа сегодняшний день пока нет записей"
    else:
        message_lines = [f"📅 <b>Запись в сервис на {today.strftime('%d.%m.%Y')} (сегодняшний день)</b>\n"]
        for appt in appointments:
            user = await rq.get_user_profile(appt.user_id)
            name = user.get('name', 'Не указано') if user else 'Не указано'
            status = "✅ Подтверждена" if appt.is_confirmed else "❌ Не подтверждена"
            message_lines.append(
                "—————————\n"
                f"<b>Имя клиента:</b> {name}\n"
                f"<b>Номер телефона:<b> <code>{appt.mobile_phone}</code>\n"
                f"<b>Время записи:<b> {appt.date_time.strftime('%H:%M')}\n"
                f"<b>Статус:<b> {status}\n"
            )
        message = "\n".join(message_lines) + "—————————"
    try:
        msg = await bot.send_message(chat_id=CHANNEL_ID_DAILY, text=message, parse_mode="HTML")
        await rq.set_daily_message_id(msg.message_id)
        return msg.message_id
    except Exception as e:
        print(f"Ошибка отправки ежедневного отчёта: {e}")
        return None

async def notify_upcoming_appointments(bot: Bot):
    """Отправляет уведомления пользователям за 3 часа до записи."""
    current_time = datetime.now(EKATERINBURG_TZ)
    appointments = await rq.get_upcoming_appointments_for_notification(current_time)
    for appt in appointments:
        keyboard = await kb.get_approved_appointment_keyboard(appt.user_id)
        message = (
            f"⏰ <b>У вас запись в сервис</b> на {appt.date_time.strftime('%H:%M %d.%m.%Y')}\n"
            f"🛠️ <b>Услуга:</b> {appt.service.split('. Тип машины')[0] if '. Тип машины' in appt.service else appt.service}\n\n"
            "<b>Вы приедете?</b> 🤔"
        )
        try:
            await bot.send_message(chat_id=appt.user_id, text=message, reply_markup=keyboard)
            await rq.set_notified(appt.user_id)
        except Exception as e:
            print(f"Ошибка отправки уведомления пользователю {appt.user_id}: {e}")

async def setup_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler(timezone=EKATERINBURG_TZ)
    scheduler.add_job(send_daily_appointments, trigger=CronTrigger(hour=7, minute=0), args=[bot], max_instances=1)
    scheduler.add_job(notify_upcoming_appointments, trigger=CronTrigger(hour="7-19", minute=0), args=[bot], max_instances=1)
    scheduler.add_job(send_monthly_report, trigger=CronTrigger(day="last", hour=18, minute=0), args=[bot], max_instances=1)
    scheduler.start()

    return scheduler