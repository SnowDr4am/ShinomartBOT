import os
import uuid
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
from typing import Optional
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram import F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from app.handlers.main import admin_router
from app.handlers.admin.admin import cmd_job
import app.keyboards.admin.admin as kb
import app.database.admin_requests as rq

Path("media/temp").mkdir(parents=True, exist_ok=True)
Path("media/promotions").mkdir(parents=True, exist_ok=True)

class AddPromotionStates(StatesGroup):
    waiting_full_text = State()
    waiting_image = State()
    waiting_short_desc = State()
    waiting_confirmation = State()

async def cleanup_temp_files(image_path: str | None):
    """Удаляет временные файлы при отмене/ошибке"""
    if image_path and os.path.exists(image_path):
        try:
            os.remove(image_path)
        except Exception as e:
            print(f"Error deleting temp file {image_path}: {e}")

async def handle_cancellation(message: Message, state: FSMContext, cleanup_path: str | None = None):
    if message.text and message.text.lower() == "отмена":
        if cleanup_path:
            await cleanup_temp_files(cleanup_path)
        await state.clear()
        await message.answer("❌ Операция отменена", parse_mode='HTML')
        await cmd_job(message)
        return True
    return False

async def save_image(file_id, bot: Bot):
    filename = f"promo_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.jpg"
    file_path = f"media/temp/{filename}"

    try:
        file = await bot.get_file(file_id)
        await bot.download_file(file.file_path, file_path)
        return file_path
    except Exception as e:
        raise Exception(f"Не удалось сохранить изображение: {str(e)}")

@contextmanager
def temp_file_manager(file_path: Optional[str]):
    try:
        yield file_path
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                print(f"Ошибка при удалении файла - {e}")

def validate_short_description(text: str) -> None:
    if len(text) > 100:
        raise ValueError("Описание слишком длинное (макс. 100 символов)")

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

@admin_router.callback_query(F.data == 'addPromotion')
async def start_adding_promotion(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(AddPromotionStates.waiting_full_text)
    await callback.message.answer(
        "📝 Введите <b>полный текст</b> акции\n\n"
        "Или напишите <code>отмена</code> для отмены",
        parse_mode="HTML"
    )

@admin_router.message(AddPromotionStates.waiting_full_text)
async def process_full_text(message: Message, state: FSMContext):
    if await handle_cancellation(message, state):
        return

    await state.update_data(full_text=message.text.strip())
    await state.set_state(AddPromotionStates.waiting_image)
    await message.answer(
        "🖼 Отправьте <b>изображение</b> для акции\n"
        "Или отправьте <code>-</code> без изображения\n\n"
        "Напишите <code>отмена</code> для отмены",
        parse_mode="HTML"
    )

@admin_router.message(AddPromotionStates.waiting_image)
async def process_image(message: Message, state: FSMContext):
    if await handle_cancellation(message, state):
        return

    image_path = None
    if message.text and message.text.strip() == '-':
        pass
    elif message.photo:
        with temp_file_manager(image_path) as temp_path:
            try:
                image_path = await save_image(message.photo[-1].file_id, message.bot)
            except ValueError as e:
                await message.answer(f"❌ Ошибка: {str(e)}")
                return
    else:
        await message.answer("⚠️ Пожалуйста, отправьте изображение или <code>-</code>")
        return

    await state.update_data(image_path=image_path)
    await state.set_state(AddPromotionStates.waiting_short_desc)
    await message.answer(
        "🔤 Введите <b>краткое описание</b> акции (макс. 100 символов)\n\n"
        "Напишите <code>отмена</code> для отмены",
        parse_mode='HTML'
    )

@admin_router.message(AddPromotionStates.waiting_short_desc)
async def process_short_desc(message: Message, state: FSMContext):
    if await handle_cancellation(message, state, (await state.get_data()).get('image_path')):
        return

    try:
        validate_short_description(message.text)
    except ValueError as e:
        await message.answer(f"⚠️ {str(e)}")
        return

    await state.update_data(short_description=message.text)
    data = await state.get_data()
    caption = format_promo_caption(
        title="Превью акции",
        short_desc=data['short_description'],
        full_text=data['full_text']
    )

    try:
        if data.get('image_path'):
            photo = FSInputFile(data['image_path'])
            await message.answer_photo(
                photo=photo,
                caption=caption,
                parse_mode='HTML',
                reply_markup=kb.confirm_new_promotion
            )
        else:
            await message.answer(
                text=caption,
                parse_mode='HTML',
                reply_markup=kb.confirm_new_promotion
            )
        await state.set_state(AddPromotionStates.waiting_confirmation)
    except Exception as e:
        await message.answer(f"❌ Ошибка при создании превью: {str(e)}")
        await cleanup_temp_files(data.get('image_path'))
        await state.clear()

@admin_router.callback_query(AddPromotionStates.waiting_confirmation, F.data.startswith("confirmNewPromotion"))
async def handle_confirmation(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    success = False

    action = callback.data.split(":")[1]
    data = await state.get_data()

    try:
        if action == "yes":
            if data.get("image_path"):
                filename = os.path.basename(data['image_path'])
                permanent_path = f"media/promotions/{filename}"

                try:
                    os.rename(data['image_path'], permanent_path)
                    data['image_path'] = permanent_path
                except Exception as e:
                    print(f"Не удалось сохранить изображение: {e}")

            await rq.add_promotion(data)
            await callback.message.delete()
            await callback.message.answer("✅ Акция успешно добавлена!")
            success = True
        else:
            await callback.message.answer("❌ Добавление отменено")
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}")
    finally:
        if not success and data.get('image_path'):
            await cleanup_temp_files(data['image_path'])

        await state.clear()
        await cmd_job(callback.message)