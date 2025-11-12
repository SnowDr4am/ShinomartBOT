from aiogram import F
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
import os

from app.handlers.main import user_router
import app.database.StorageCellsService as storage_service
import app.database.requests as rq
from app.utils.word import generate_storage_word_document


@user_router.callback_query(F.data.startswith("storage_confirm_handover:"))
async def handle_storage_confirmation(callback: CallbackQuery):
    """Обработка подтверждения/отклонения сдачи шин на хранение"""
    await callback.answer()
    
    parts = callback.data.split(":")
    cell_storage_id = int(parts[1])
    action = parts[2]  # yes или no
    
    cell_storage = await storage_service.get_cell_storage_by_id(cell_storage_id)
    if not cell_storage:
        return await callback.message.edit_text("❌ Запись не найдена!")
    
    if action == "yes":
        # Подтверждаем сдачу
        await storage_service.update_confirmation_status(cell_storage_id, "confirmed")
        
        # Получаем данные для генерации файла
        user_data = await rq.get_user_by_id(cell_storage.user_id)
        worker_data = await rq.get_user_by_id(cell_storage.worker_id)
        
        # Генерируем Word документ
        word_file = await generate_storage_word_document(cell_storage, user_data, worker_data)
        
        # Отправляем файл клиенту
        if word_file and os.path.exists(word_file):
            document = FSInputFile(word_file)
            await callback.message.answer_document(
                document=document,
                caption="📄 <b>Документ о сдаче шин на хранение</b>",
                parse_mode="HTML"
            )
        
        # Отправляем файл работнику
        try:
            worker_tg_id = int(worker_data.user_id)
            if word_file and os.path.exists(word_file):
                document = FSInputFile(word_file)
                await callback.bot.send_document(
                    chat_id=worker_tg_id,
                    document=document,
                    caption=f"📄 <b>Документ о сдаче шин на хранение</b>\n\n"
                           f"Ячейка №{getattr(await storage_service.get_cell(cell_storage.cell_id), 'value', None) or cell_storage.cell_id}\n"
                           f"Клиент: {user_data.name}",
                    parse_mode="HTML"
                )
        except Exception as e:
            print(f"⚠️ Ошибка при отправке файла работнику: {e}")
        
        await callback.message.edit_text(
            "✅ <b>Сдача шин на хранение подтверждена!</b>\n\n"
            "Ваши шины приняты на хранение.",
            parse_mode="HTML"
        )
    else:
        # Отклоняем - удаляем данные из ячейки
        await storage_service.delete_cell_storage(cell_storage.cell_id)
        await callback.message.edit_text(
            "❌ <b>Сдача шин отклонена</b>\n\n"
            "Данные о хранении удалены. Обратитесь к работнику для уточнения деталей.",
            parse_mode="HTML"
        )


@user_router.callback_query(F.data.startswith("storage_confirm_pickup:"))
async def handle_pickup_confirmation(callback: CallbackQuery):
    """Обработка подтверждения/отклонения получения шин"""
    await callback.answer()
    
    parts = callback.data.split(":")
    cell_storage_id = int(parts[1])
    action = parts[2]  # yes или no
    
    cell_storage = await storage_service.get_cell_storage_by_id(cell_storage_id)
    if not cell_storage:
        return await callback.message.edit_text("❌ Запись не найдена!")
    
    if action == "yes":
        # Подтверждаем получение - освобождаем ячейку
        await storage_service.update_confirmation_status(cell_storage_id, "confirmed")
        await storage_service.delete_cell_storage(cell_storage.cell_id)
        await callback.message.edit_text(
            "✅ <b>Получение шин подтверждено!</b>\n\n"
            "Ячейка освобождена. Спасибо за использование наших услуг!",
            parse_mode="HTML"
        )
    else:
        # Отклоняем - возвращаем статус на confirmed, данные остаются в ячейке
        await storage_service.update_confirmation_status(cell_storage_id, "confirmed")
        # Возвращаем action_type обратно на handover
        await storage_service.save_or_update_cell_storage(
            cell_id=cell_storage.cell_id,
            worker_id=cell_storage.worker_id,
            user_id=cell_storage.user_id,
            storage_type=cell_storage.storage_type,
            price=cell_storage.price,
            description=cell_storage.description,
            scheduled_month=cell_storage.scheduled_month,
            meta_data=cell_storage.meta_data,
            action_type="handover",
            confirmation_status="confirmed"
        )
        await callback.message.edit_text(
            "❌ <b>Получение шин отклонено</b>\n\n"
            "Данные о хранении сохранены. Обратитесь к работнику для уточнения деталей.",
            parse_mode="HTML"
        )


@user_router.callback_query(F.data.startswith("storage_confirm_free:"))
async def handle_free_confirmation(callback: CallbackQuery):
    """Обработка подтверждения/отклонения освобождения ячейки"""
    await callback.answer()
    
    parts = callback.data.split(":")
    cell_storage_id = int(parts[1])
    action = parts[2]  # yes или no
    
    cell_storage = await storage_service.get_cell_storage_by_id(cell_storage_id)
    if not cell_storage:
        return await callback.message.edit_text("❌ Запись не найдена!")
    
    if action == "yes":
        # Подтверждаем освобождение - удаляем запись хранения
        await storage_service.update_confirmation_status(cell_storage_id, "confirmed")
        await storage_service.delete_cell_storage(cell_storage.cell_id)
        await callback.message.edit_text(
            "✅ <b>Освобождение ячейки подтверждено!</b>\n\n"
            "Ячейка освобождена. Спасибо за использование наших услуг!",
            parse_mode="HTML"
        )
    else:
        # Отклоняем - возвращаем статус на confirmed, данные остаются в ячейке
        await storage_service.update_confirmation_status(cell_storage_id, "confirmed")
        # Возвращаем action_type обратно на handover
        await storage_service.save_or_update_cell_storage(
            cell_id=cell_storage.cell_id,
            worker_id=cell_storage.worker_id,
            user_id=cell_storage.user_id,
            storage_type=cell_storage.storage_type,
            price=cell_storage.price,
            description=cell_storage.description,
            scheduled_month=cell_storage.scheduled_month,
            meta_data=cell_storage.meta_data,
            action_type="handover",
            confirmation_status="confirmed"
        )
        await callback.message.edit_text(
            "❌ <b>Освобождение ячейки отклонено</b>\n\n"
            "Данные о хранении сохранены. Обратитесь к работнику для уточнения деталей.",
            parse_mode="HTML"
        )

