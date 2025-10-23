from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
import pytz
from app.database.models import async_session, QRCode
from sqlalchemy import delete
import app.database.requests as rq
from config import CHANNEL_ID_DAILY
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
        f"👥 <b>Новых пользователей:</b> {report_data.get('new_users', 0)}\n"
        f"🛒 <b>Количество продаж:</b> {report_data.get('sales_count', 0)}\n"
        f"💸 <b>Сумма всех транзакций:</b> {report_data.get('sales_amount', 0):.2f} руб.\n"
        f"🎁 <b>Начислено бонусов:</b> {report_data.get('bonuses_added', 0):.2f}\n"
        f"🔥 <b>Списано бонусов:</b> {report_data.get('bonuses_spent', 0):.2f}\n\n"
        f"✨ <i>Отчёт сформирован {now.strftime('%d.%m.%Y в %H:%M')}</i>"
    )
    try:
        await bot.send_message(chat_id=CHANNEL_ID_DAILY, text=report, parse_mode="HTML")
        print("Ежемесячный отчёт отправлен")
    except Exception as e:
        print(f"Ошибка отправки отчёта: {e}")

async def clear_qr_codes():
    async with async_session() as session:
        try:
            await session.execute(delete(QRCode))
            await session.commit()
        except Exception as e:
            print(f"Ошибка при удалении QR-кодов: {e}")
            await session.rollback()

async def setup_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler(timezone=EKATERINBURG_TZ)
    scheduler.add_job(send_monthly_report, trigger=CronTrigger(day="last", hour=18, minute=0), args=[bot], max_instances=1)
    scheduler.add_job(clear_qr_codes, trigger=CronTrigger(hour=00, minute=00), max_instances=1)
    scheduler.start()

    return scheduler