import os
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram import F
from aiogram.types import Message, CallbackQuery, FSInputFile
from app.handlers.main import admin_router
from app.handlers.admin.admin import cmd_job, show_control_promotions
import app.keyboards.admin.admin as kb
import app.database.admin_requests as rq
import app.database.requests as c_rq

class EditPromotionStates(StatesGroup):
    waiting_full_text = State()
    waiting_short_desc = State()
    waiting_new_image = State()

def format_promo_caption(
    title: str,
    status: str | None = None,
    short_desc: str | None = None,
    full_text: str | None = None
) -> str:
    caption = f"<b>{title}</b>\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
    if status:
        caption += f"<b>Статус:</b> {status}\n\n"
    if short_desc:
        caption += f"<b>Краткое описание:</b> {short_desc}\n\n"
    if full_text:
        caption += f"<b>Полный текст:</b>\n{full_text}"
    return caption

async def cleanup_temp_files(image_path: str | None):
    """Удаляет временные файлы при отмене/ошибке"""
    if image_path and os.path.exists(image_path):
        try:
            os.remove(image_path)
        except OSError as e:
            print(f"Ошибка при удалении файла: {e}")

async def handle_cancellation(message: Message, state: FSMContext, cleanup_path: str | None = None):
    if message.text and message.text.lower() == "отмена":
        if cleanup_path:
            await cleanup_temp_files(cleanup_path)
        await state.clear()
        await message.answer("❌ Изменение отменено", parse_mode='HTML')
        await cmd_job(message)
        return True
    return False

@admin_router.callback_query(F.data.startswith("editPromo"))
async def start_edit_promotion(callback: CallbackQuery):
    await callback.answer()

    await callback.message.delete()
    promo_id = callback.data.split(":")[1]

    promotion = await c_rq.get_promo_by_id(promo_id)

    status = "✅ Видима" if promotion.is_active else "❌ Скрыта"
    caption = format_promo_caption(
        title="Управление акцией",
        status=status,
        short_desc=promotion.short_description,
        full_text=promotion.full_description
    )

    try:
        keyboard = await kb.get_promotion_management(promo_id)
        if promotion.image_path:
            try:
                photo = FSInputFile(promotion.image_path)
                await callback.message.answer_photo(
                    photo=photo,
                    caption=caption,
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
            except Exception as e:
                await callback.message.answer(
                    text=f"⚠️ Не удалось загрузить изображение\n\n{caption}",
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
        else:
            await callback.message.answer(
                text=caption,
                parse_mode='HTML',
                reply_markup=keyboard
            )
    except Exception as e:
        await callback.message.answer(f"⚠️ Возникла ошибка при отправке поста:\n\n{e}")

@admin_router.callback_query(F.data.startswith("promotionEdit"))
async def process_promotion_edit(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    _, action, promo_id = callback.data.split(":")
    await state.update_data(promo_id=promo_id)

    if action == 'full_text':
        await state.set_state(EditPromotionStates.waiting_full_text)
        await callback.message.answer(
            "📝 Введите новый полный текст акции\n\n"
            "Или напишите <code>отмена</code> для отмены",
            parse_mode="HTML"
        )
    elif action == "short_text":
        await state.set_state(EditPromotionStates.waiting_short_desc)
        await callback.message.answer(
            "🔤 Введите новое краткое описание (макс. 100 символов)\n\n"
            "Или напишите <code>отмена</code> для отмены",
            parse_mode="HTML"
        )
    elif action == "image":
        await state.set_state(EditPromotionStates.waiting_new_image)
        await callback.message.answer(
            "🖼 Отправьте новое изображение для акции\n\n"
            "Или напишите <code>отмена</code> для отмены",
            parse_mode="HTML"
        )
    elif action == 'toggle':
        promo = await c_rq.get_promo_by_id(promo_id)
        new_status = not promo.is_active
        await rq.update_promotion(promo_id, is_active=new_status)
        status = "✅ Акция теперь видима" if new_status else "❌ Акция теперь скрыта"
        keyboard = await kb.get_promotion(promo_id)
        await callback.message.answer(status, reply_markup=keyboard)
    elif action == 'delete':
        keyboard = await kb.confirm_delete_promotion(promo_id)
        await callback.message.answer(
            "⚠️ Вы уверены, что хотите удалить эту акцию?",
            reply_markup=keyboard
        )

@admin_router.callback_query(F.data.startswith("confirmDeletePromotion"))
async def confirm_delete_promo(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    promo_id = int(callback.data.split(":")[1])

    success = await rq.delete_promotion(promo_id)
    if success:
        await callback.message.answer("✅ Акция успешно удалена")
        await show_control_promotions(callback, state)
    else:
        await callback.message.answer("❌ Не удалось удалить акцию")

@admin_router.message(EditPromotionStates.waiting_full_text)
async def process_new_full_text(message: Message, state: FSMContext):
    if await handle_cancellation(message, state):
        return

    data = await state.get_data()
    promo_id = data['promo_id']

    await rq.update_promotion(promo_id, full_description=message.text.strip())
    await state.clear()

    keyboard = await kb.get_promotion(promo_id)
    await message.answer("✅ Полный текст акции обновлен!", reply_markup=keyboard)

@admin_router.message(EditPromotionStates.waiting_short_desc)
async def process_new_short_text(message: Message, state: FSMContext):
    if await handle_cancellation(message, state):
        return
    if len(message.text.strip()) > 100:
        await message.answer("⚠️ Описание слишком длинное (макс. 100 символов)")
        return

    data = await state.get_data()
    promo_id = data['promo_id']

    await rq.update_promotion(promo_id, short_description=message.text.strip())
    await state.clear()

    keyboard = await kb.get_promotion(promo_id)
    await message.answer("✅ Краткое описание обновлено!", reply_markup=keyboard)

@admin_router.message(EditPromotionStates.waiting_new_image)
async def process_new_image(message: Message, state: FSMContext):
    if await handle_cancellation(message, state):
        return
    if not message.photo:
        await message.answer("⚠️ Пожалуйста, отправьте изображение")
        return

    data = await state.get_data()
    promo_id = data['promo_id']

    promo = await rq.get_promo_by_id(promo_id)
    if promo.image_path:
        image_path = promo.image_path
        if os.path.exists(image_path):
            os.remove(image_path)
    else:
        filename = f"promo_{promo_id}.jpg"
        image_path = f"media/promotions/{filename}"
        os.makedirs(os.path.dirname(image_path), exist_ok=True)

    file_id = message.photo[-1].file_id
    file = await message.bot.get_file(file_id)
    await message.bot.download_file(file.file_path, image_path)
    if not promo.image_path or promo.image_path != image_path:
        await rq.update_promotion(promo_id, image_path=image_path)
    await state.clear()

    keyboard = await kb.get_promotion(promo_id)
    await message.answer("✅ Изображение акции обновлено!", reply_markup=keyboard)

