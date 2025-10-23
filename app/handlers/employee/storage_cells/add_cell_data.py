import os

from aiogram import F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from datetime import datetime, date

from app.handlers.main import employee_router, media_router
from app.utils.states import StorageCellStates
import app.keyboards.employee.storage_cells.add_cell_data as kb
import app.database.StorageCellsService as storage_service
import app.database.requests as rq
from app.utils.func import update_message_ids_in_state, delete_message_in_state
from app.utils.word import generate_storage_word_document


# ==================== Заполнение пустой ячейки ====================
@employee_router.callback_query(F.data.startswith("start_add_cell_data:"))
async def handle_start_add_cell_data(callback: CallbackQuery, state: FSMContext):
    cell_id = int(callback.data.split(":")[-1])
    await state.update_data(cell_id=cell_id)

    sent = await callback.message.edit_text(
        "📱 <b>Введите номер телефона клиента</b>\n"
        "Пример: +7 999 123-45-67\n\n",
        parse_mode="HTML",
        reply_markup=kb.generate_simple_keyboard("◀️ Назад", f"storage_cell:{cell_id}")
    )
    await update_message_ids_in_state(state, "action_message_ids", sent.message_id)
    await state.set_state(StorageCellStates.waiting_phone_number)

@employee_router.message(StorageCellStates.waiting_phone_number)
async def process_phone_number(message: Message, state: FSMContext):
    """Обработка номера телефона"""
    await update_message_ids_in_state(state, "action_message_ids", message.message_id)
    phone = message.text.strip()

    # Проверяем, существует ли пользователь
    user_exists = await rq.check_mobile_phone(phone)

    if not user_exists:
        sent = await message.answer(
            "❌ <b>Пользователь с таким номером не найден!</b>\n\n"
            "Пожалуйста, введите корректный номер телефона:",
            parse_mode="HTML"
        )
        return await update_message_ids_in_state(state, "action_message_ids", sent.message_id)

    # Сохраняем номер телефона
    await state.update_data(user_phone=phone)

    sent = await message.answer(
        "🛞 <b>Выберите тип хранения:</b>",
        parse_mode="HTML",
        reply_markup=kb.storage_type_keyboard
    )
    await state.set_state(StorageCellStates.waiting_storage_type)
    await update_message_ids_in_state(state, "action_message_ids", sent.message_id)


@employee_router.callback_query(StorageCellStates.waiting_storage_type, F.data.startswith("storage_type:"))
async def process_storage_type(callback: CallbackQuery, state: FSMContext):
    """Обработка типа хранения"""
    storage_type = callback.data.split(":")[1]

    # Определяем цену
    if storage_type == "Шины с дисками":
        price = 3500
    else:
        price = 3000

    await state.update_data(storage_type=storage_type, price=price)

    sent = await callback.message.edit_text(
        f"✅ Выбран тип: <b>{storage_type}</b>\n"
        f"💰 Цена: <b>{price} руб.</b>\n\n"
        "📝 <b>Введите описание:</b>\n"
        "<i>(например: Nokian 205/55 R16)</i>\n\n"
        "<i>Для отмены напишите 'отмена'</i>",
        parse_mode="HTML"
    )
    await state.set_state(StorageCellStates.waiting_description)
    await update_message_ids_in_state(state, "action_message_ids", sent.message_id)


@employee_router.message(StorageCellStates.waiting_description)
async def process_description(message: Message, state: FSMContext):
    """Обработка описания"""
    await update_message_ids_in_state(state, "action_message_ids", message.message_id)

    description = message.text.strip()
    await state.update_data(description=description)

    # Показываем клавиатуру с месяцами
    current_year = datetime.now().year
    keyboard = await kb.generate_month_keyboard(current_year)

    await state.update_data(current_year=current_year)

    await message.answer(
        "📅 <b>Выберите срок хранения:</b>\n"
        "<i>(до какого месяца)</i>",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await state.set_state(StorageCellStates.waiting_scheduled_month)


@employee_router.callback_query(StorageCellStates.waiting_scheduled_month, F.data.startswith("storage_year:"))
async def change_year(callback: CallbackQuery, state: FSMContext):
    """Смена года в календаре"""
    await callback.answer()

    year = int(callback.data.split(":")[1])
    await state.update_data(current_year=year)

    keyboard = await kb.generate_month_keyboard(year)

    await callback.message.edit_text(
        "📅 <b>Выберите срок хранения:</b>\n"
        "<i>(до какого месяца)</i>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@employee_router.callback_query(StorageCellStates.waiting_scheduled_month, F.data.startswith("storage_month:"))
async def process_scheduled_month(callback: CallbackQuery, state: FSMContext):
    """Обработка выбранного месяца"""
    parts = callback.data.split(":")
    year = int(parts[1])
    month = int(parts[2])

    scheduled_date = date(year, month, 1)
    await state.update_data(scheduled_month=scheduled_date)

    sent = await callback.message.edit_text(
        f"✅ Срок хранения: <b>{scheduled_date.strftime('%B %Y')}</b>\n\n"
        "📸 <b>Отправьте фотографии:</b>\n"
        "<i>(можно отправить несколько фото)</i>\n\n"
        "После отправки всех фото напишите <b>'готово'</b>",
        parse_mode="HTML"
    )
    await state.update_data(photos=[])
    await state.set_state(StorageCellStates.waiting_photos)
    await update_message_ids_in_state(state, "action_message_ids", sent.message_id)


@media_router.message(StorageCellStates.waiting_photos)
async def handle_photos(message: Message, state: FSMContext, album: list[Message] = None):
    """Сбор фотографий"""
    data = await state.get_data()
    current_photos = data.get("photos", [])

    if album:
        for msg in album:
            if msg.photo:
                file_id = msg.photo[-1].file_id
                current_photos.append(file_id)
            await update_message_ids_in_state(state, "action_message_ids", msg.message_id)

        await state.update_data(photos=current_photos)
        sent = await message.answer(
            f"📷 <b>Загружено фото:</b> {len(current_photos)}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"Можете добавить ещё или нажмите <b>«Готово»</b> для продолжения",
            parse_mode='HTML',
            reply_markup=kb.cell_data_complete_photo_report
        )
        return await update_message_ids_in_state(state, "action_message_ids", sent.message_id)

    if message.photo:
        file_id = message.photo[-1].file_id
        current_photos.append(file_id)
        await state.update_data(photos=current_photos)
        await update_message_ids_in_state(state, "action_message_ids", message.message_id)
        sent = await message.answer(
            f"📷 <b>Загружено фото:</b> {len(current_photos)}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"Можете добавить ещё или нажмите <b>«Готово»</b> для продолжения",
            parse_mode='HTML',
            reply_markup=kb.cell_data_complete_photo_report
        )
        return await update_message_ids_in_state(state, "action_message_ids", sent.message_id)

    sent = await message.answer("⚠️ Пожалуйста, отправьте фото или нажмите ✅ Готово",
                                reply_markup=kb.cell_data_complete_photo_report)
    await update_message_ids_in_state(state, "action_message_ids", message.message_id)
    await update_message_ids_in_state(state, "action_message_ids", sent.message_id)


@employee_router.callback_query(F.data == "storage_cells:complete_photo_report")
async def finish_photo_collection(callback: CallbackQuery, state: FSMContext):
    """Завершение сбора фотографий"""
    data = await state.get_data()
    photos = data.get("photos", [])

    if not photos:
        return await callback.answer(
            "⚠️ Необходимо добавить хотя бы одну фотографию!\n"
            "Отправьте фото или напишите 'отмена' для отмены операции.",
            show_alert=True
        )

    # Сохраняем информацию в базу данных
    cell_id = data.get("cell_id")
    user_phone = data.get("user_phone")
    storage_type = data.get("storage_type")
    price = data.get("price")
    description = data.get("description")
    scheduled_month = data.get("scheduled_month")

    # Получаем информацию о пользователе
    user_data = await rq.get_user_by_phone(user_phone)
    worker_data = await rq.get_user_by_tg_id(callback.from_user.id)

    meta_data = {"photos": photos}

    # Сохраняем в базу
    cell_storage = await storage_service.save_or_update_cell_storage(
        cell_id=cell_id,
        worker_id=worker_data.id,
        user_id=user_data.id,
        storage_type=storage_type,
        price=price,
        description=description,
        scheduled_month=scheduled_month,
        meta_data=meta_data
    )

    # Генерируем Word документ
    word_file = await generate_storage_word_document(cell_storage, user_data, worker_data)

    if word_file and os.path.exists(word_file):
        document = FSInputFile(word_file)
        await callback.message.answer_document(
            document=document,
            caption=f"Файл для отчета",
            reply_markup=kb.delete_message_keyboard
        )

    await delete_message_in_state(callback.bot, state, callback.from_user.id)
    await state.clear()

    await callback.message.answer(
        f"Ячейка #{cell_id} успешно заполнена",
        parse_mode="HTML",
        reply_markup=kb.generate_simple_keyboard("Назад", "storage_open_cells")
    )