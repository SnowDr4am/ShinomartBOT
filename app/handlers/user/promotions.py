from aiogram import F
from aiogram.types import CallbackQuery, FSInputFile
from app.handlers.main import user_router
import app.keyboards.user.user as kb
import app.database.requests as rq

@user_router.callback_query(F.data.startswith("viewPromotion"))
async def view_promotion(callback: CallbackQuery):
    await callback.answer()
    await callback.message.delete()

    promo_id = callback.data.split(":")[1]
    promotion = await rq.get_promo_by_id(promo_id)

    caption = (
        f"<b>{promotion.short_description}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{promotion.full_description}"
    )

    if promotion.image_path:
        try:
            photo = FSInputFile(promotion.image_path)
            await callback.message.answer_photo(
                photo=photo,
                caption=caption,
                parse_mode='HTML',
                reply_markup=kb.back_to_all_promotions
            )
        except Exception as e:
            await callback.message.answer(
                text=f"📌 {caption}\n\n⚠️ Изображение временно недоступно",
                parse_mode='HTML',
                reply_markup=kb.back_to_all_promotions
            )
    else:
        await callback.message.answer(
            text=caption,
            parse_mode='HTML',
            reply_markup=kb.back_to_all_promotions
        )
