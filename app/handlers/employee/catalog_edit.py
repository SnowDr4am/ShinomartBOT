from datetime import datetime

from aiofiles.os import replace
from aiogram import F
from aiogram.fsm.context import FSMContext

from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from app.handlers.main import user_router, employee_router
import app.database.ItemService as ItemService
import app.database.requests as rq
import app.keyboards.employee.catalog as catalog_kb

from app.utils.states import EditItemStates


@employee_router.callback_query(F.data.startswith("item_card_action"))
async def employee_edit_card_action(callback: CallbackQuery):
    await callback.answer()
    item_id = int(callback.data.split(":")[1])
    action = callback.data.split(":")[2]

    if action == "sold":
        item = await ItemService.get_item_by_id(item_id)
        if item:
            user = await rq.get_user_by_tg_id(callback.from_user.id)

            meta = item.meta_data or {}
            meta["status"] = "sold"
            meta["worker"] = user.name
            meta["sold_date"] = datetime.now().strftime("%d.%m.%Y %H:%M")

            updated_item = await ItemService.update_item(item_id, meta_data=meta)

            await callback.message.edit_text(
                f"✅ Товар <b>{updated_item.value}</b> помечен как проданный",
                parse_mode="HTML",
                reply_markup=None
            )
    else:
        keyboard = await catalog_kb.employee_edit_card_keyboard(item_id)
        await callback.message.edit_reply_markup(reply_markup=keyboard)

@employee_router.callback_query(F.data.startswith("edit_card_field"))
async def handle_edit_card_field(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    item_id = int(callback.data.split(":")[1])
    field = callback.data.split(":")[2]

    await state.update_data(item_id=item_id, field=field)

    if field == "photos":
        await callback.message.answer("📸 Отправьте новое фото (одно или несколько)\n\n"
                                      "После загрузки всех изображений нажмите 'Готово'",
                                      reply_markup=catalog_kb.success_upload_picture)
        await state.set_state(EditItemStates.waiting_photos)
    else:
        pretty_fields = {
            "value": "Название",
            "description": "Описание",
            "price": "Цена",
            "diameter": "Диаметр",
        }
        await callback.message.answer(f"✏️ Введите новое значение для поля <b>{pretty_fields.get(field, field)}:</b>",
                                      parse_mode="HTML")
        await state.set_state(EditItemStates.waiting_field_input)


@employee_router.message(EditItemStates.waiting_field_input)
async def process_text_field_edit(message: Message, state: FSMContext):
    data = await state.get_data()
    item_id = data["item_id"]
    field = data["field"]
    new_value = message.text.strip()

    item = await ItemService.get_item_by_id(item_id)
    if not item:
        await message.answer("❌ Товар не найден.")
        return

    if field == "value":
        await ItemService.update_item(item_id=item_id, value=new_value)
    else:
        meta = item.meta_data or {}
        if field == "price":
            try:
                new_value = int(new_value)
            except ValueError:
                await message.answer("❌ Пожалуйста, введите корректную цену (числом).")
                return
        meta[field] = new_value
        await ItemService.update_item(item_id=item_id, meta_data=meta)

    keyboard = await catalog_kb.view_update_card(item_id)
    await message.answer("✅ Поле успешно обновлено", reply_markup=keyboard)
    await state.clear()

@user_router.message(EditItemStates.waiting_photos)
async def handle_edit_photos(message: Message, state: FSMContext):
    if message.text == "✅ Готово":
        data = await state.get_data()
        item_id = data.get("item_id")
        photos = data.get("photos", [])

        if not item_id or not photos:
            await message.answer("❌ Не удалось сохранить фото. Попробуйте ещё раз.")
            return

        item = await ItemService.get_item_by_id(item_id)
        if not item:
            await message.answer("❌ Товар не найден.")
            return

        meta = item.meta_data or {}
        meta["photos"] = photos

        await ItemService.update_item(item_id=item.id, meta_data=meta)

        await message.answer(".", reply_markup=ReplyKeyboardRemove())
        await message.delete()

        keyboard = await catalog_kb.view_update_card(item_id)
        await message.answer(
            f"✅ Фотографии успешно обновлены для товара <b>{item.value}</b>.",
            parse_mode="HTML",
            reply_markup=keyboard
        )

        await state.clear()
        return

    if not message.photo:
        await message.answer("⚠️ Пожалуйста, отправьте фото или нажмите ✅ Готово, если закончили.")
        return

    data = await state.get_data()
    current_photos = data.get("photos", [])

    if len(current_photos) >= 10:
        await message.answer("⚠️ Максимум 10 фото. Нажмите ✅ Готово для продолжения.")
        return

    new_photo_id = message.photo[-1].file_id
    current_photos.append(new_photo_id)

    await state.update_data(photos=current_photos)