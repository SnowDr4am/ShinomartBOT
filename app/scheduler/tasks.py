from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
import app.database.requests as kb
from app.servers.config import CHANNEL_ID
from datetime import datetime

async def send_monthly_report(bot: Bot):
    now = datetime.now()
    year, month = now.year, now.month

    report_data = await kb.get_monthly_report(year, month)

    month_names = {
        1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
        5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
        9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
    }
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
        await bot.send_message(chat_id=CHANNEL_ID, text=report, parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка отправки отчёта: {e}")

async def setup_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        send_monthly_report,
        trigger=CronTrigger(day="last", hour=18, minute=00),
        args=[bot]
    )
    scheduler.start()

    return scheduler