from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram.utils.media_group import MediaGroupBuilder

from app.handlers.main import user_router, admin_router, employee_router
import app.database.ItemService as ItemService
import app.database.requests as rq
import app.keyboards.employee.catalog as catalog_kb
from app.utils.states import CreateItemStates
from app.handlers.user.user import main_menu

from app.handlers.user.catalog.utils import get_category


@employee_router.message(F.text=='➕ Добавить Б/У резину или диски')
async def start_create_new_item(message: Message):
    await message.answer(
        "📦 <b>Добавление новой позиции</b>\n\n"
        "Выберите, что вы хотите добавить:",
        parse_mode="HTML",
        reply_markup=catalog_kb.employee_item_type_view
    )


@employee_router.callback_query(F.data.startswith("create_item:"))
async def create_type_id_chosen(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    arg = callback.data.split(":")[1]
    category_name, type_id = await get_category(arg)

    await state.update_data(category_name=category_name, type_id=type_id)

    categories = await ItemService.get_all_categories(type_id)
    keyboard = await catalog_kb.get_create_radius_keyboard(categories, type_id)

    await callback.message.edit_text(
        f"📍 <b>Тип:</b> {category_name}\n\n"
        f"🔘 Выберите <b>диаметр</b> из доступных вариантов ниже:",
        parse_mode='HTML',
        reply_markup=keyboard
    )


@user_router.callback_query(F.data.startswith("create_radius:"))
async def submit_radius_chosen(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    type_id = int(callback.data.split(":")[1])
    category_id = int(callback.data.split(":")[2])
    await state.update_data(category_id=category_id)

    data = await state.get_data()
    category_name = data["category_name"]

    if type_id == 1:
        await callback.message.edit_text(
            f"❄️ <b>{category_name}</b> — укажите сезон использования:\n\n"
            "Выберите один из вариантов ниже 👇",
            parse_mode='HTML',
            reply_markup=catalog_kb.employee_season_view
        )
    else:
        await callback.message.edit_text(
            "🏷 <b>Введите название бренда</b>\n\n"
            "🛑 Напишите <code>отмена</code>, чтобы выйти на любом этапе.",
            parse_mode='HTML'
        )
        await state.set_state(CreateItemStates.waiting_brand)

@employee_router.callback_query(F.data.startswith("create_item_season:"))
async def handle_tires_season(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    season = callback.data.split(":")[1]
    await state.update_data(season=season)

    await callback.message.edit_text(
        "🏷 <b>Введите название бренда</b>\n\n"
        "🛑 Напишите <code>отмена</code>, чтобы выйти на любом этапе.",
        parse_mode='HTML'
    )
    await state.set_state(CreateItemStates.waiting_brand)


@employee_router.message(CreateItemStates.waiting_brand)
async def process_brand(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text:
        await message.answer("⚠️ Введите корректное название бренда или 'отмена'.")
        return

    await state.update_data(brand=text)
    await message.answer(
        "🛠 Опишите состояние / износ / дефекты\n"
        "Введите 'отмена' для прерывания."
    )
    await state.set_state(CreateItemStates.waiting_description)


@employee_router.message(CreateItemStates.waiting_description)
async def process_description(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text:
        await message.answer("⚠️ Пожалуйста, введите описание или 'отмена'.")
        return

    await state.update_data(description=text)
    await message.answer(
        "💰 Введите цену в рублях за 1 шт. (только цифры)\n"
        "Пример: <code>4500</code>",
        parse_mode='HTML'
    )
    await state.set_state(CreateItemStates.waiting_price)


@employee_router.message(CreateItemStates.waiting_price)
async def process_price(message: Message, state: FSMContext):
    text = message.text.strip()

    if not text.isdigit():
        await message.answer("⚠️ Введите только число — цена в рублях.")
        return

    await state.update_data(price=int(text))
    await message.answer(
        "📸 Отправьте до 10 фото.\nПосле загрузки нажмите <b>✅ Готово</b>.",
        reply_markup=catalog_kb.success_upload_picture,
        parse_mode='HTML'
    )
    await state.update_data(photos=[])
    await state.set_state(CreateItemStates.waiting_picture)


@employee_router.message(CreateItemStates.waiting_picture)
async def handle_photos(message: Message, state: FSMContext):
    if message.text == "✅ Готово":
        await message.answer("⏳ Формирую предпросмотр...", reply_markup=ReplyKeyboardRemove())
        await preview_create_employee(message, state)
        return

    if not message.photo:
        await message.answer("⚠️ Отправьте фото или нажмите ✅ Готово.")
        return

    data = await state.get_data()
    current_photos = data.get("photos", [])

    if len(current_photos) >= 10:
        await message.answer("📛 Вы загрузили максимум 10 фото.")
        return

    file_id = message.photo[-1].file_id
    current_photos.append(file_id)

    await state.update_data(photos=current_photos)


async def preview_create_employee(message: Message, state: FSMContext):
    data = await state.get_data()

    category = await ItemService.get_category_by_id(int(data["category_id"]))
    type_label = "Б/У Резина" if data["type_id"] == 1 else "Б/У Диски"

    caption = (
        f"<b>🆕 Новая позиция от сотрудника</b>\n\n"
        f"<b>🛠 Тип:</b> {type_label}\n"
        f"<b>📏 Диаметр:</b> {category.value}\n"
    )

    if data["type_id"] == 1 and "season" in data:
        emoji = "☀️" if data["season"] == "summer" else "❄️"
        caption += f"<b>🗓 Сезон:</b> {emoji} { 'Лето' if data['season'] == 'summer' else 'Зима' }\n"

    caption += (
        f"<b>🏷 Бренд:</b> {data['brand']}\n"
        f"<b>📝 Описание:</b> {data['description']}\n"
        f"<b>💰 Цена:</b> {data['price']} ₽"
    )

    photos = data.get("photos", [])
    media = MediaGroupBuilder()

    for i, photo_id in enumerate(photos):
        if i == 0:
            media.add_photo(media=photo_id, caption=caption, parse_mode='HTML')
        else:
            media.add_photo(media=photo_id)

    keyboard = await catalog_kb.confirm_employee_submission_keyboard()

    await message.answer_media_group(media.build())
    await message.answer("🔍 Всё верно?", reply_markup=keyboard)


@employee_router.callback_query(F.data.startswith('create_confirm:'))
async def confirm_employee_create(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    action = callback.data.split(":")[1]
    if action == "no":
        await state.clear()
        await callback.message.edit_text("❌ Добавление отменено")
        return

    data = await state.get_data()

    await ItemService.create_item_from_employee(
        category_id=data["category_id"],
        brand=data["brand"],
        description=data["description"],
        price=data["price"],
        photos=data["photos"],
        season=data.get("season")
    )

    await state.clear()
    await callback.message.edit_text("✅ Позиция успешно добавлена в базу данных")
