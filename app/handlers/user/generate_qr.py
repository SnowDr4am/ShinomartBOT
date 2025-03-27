import qrcode
import pytz
from datetime import datetime, timedelta
from io import BytesIO
from aiogram import F, types
from aiogram.types import CallbackQuery
from app.handlers.main import user_router
import app.database.requests as rq

EKATERINBURG_TZ = pytz.timezone('Asia/Yekaterinburg')

@user_router.callback_query(F.data == "get_qrcode")
async def generate_qr(callback: CallbackQuery):
    user = await rq.get_user_by_tg_id(callback.from_user.id)
    if not user or not user.mobile_phone:
        await callback.answer("Ошибка: твой номер телефона не указан в профиле!", show_alert=True)
        return

    last_qr = await rq.get_last_qr_code(user.id)
    if last_qr and last_qr.created_at:
        now_utc = datetime.now(EKATERINBURG_TZ).astimezone(pytz.UTC)
        created_at_utc = last_qr.created_at.replace(tzinfo=pytz.UTC) if last_qr.created_at.tzinfo is None else last_qr.created_at
        if (now_utc - created_at_utc) < timedelta(minutes=30):
            await callback.answer("Ты можешь генерировать QR-код только раз в 30 минут!", show_alert=True)
            return

    qr_link = f"https://t.me/testsnowdream_bot?start={user.mobile_phone}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_link)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    qr_img.save(buffer, format="PNG")
    buffer.seek(0)

    await rq.create_qr_code(user.id, user.mobile_phone)

    await callback.message.answer_photo(
        photo=types.BufferedInputFile(buffer.getvalue(), filename="qr_code.png"),
        caption=(
            "🎉 <b>Твой QR-код готов!</b> 🔒\n"
            "⏳ Действует 30 минут — успей использовать! ✨"
        ),
        parse_mode="HTML"
    )
    await callback.answer()