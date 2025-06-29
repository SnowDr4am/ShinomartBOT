from aiogram import F
from aiogram.fsm.context import FSMContext

from aiogram.types import CallbackQuery
from app.handlers.main import user_router
import app.database.ItemService as ItemService
import app.database.requests as rq
import app.keyboards.user.catalog as catalog_kb
from aiogram.utils.media_group import MediaGroupBuilder

from .utils import *


@user_router.callback_query(F.data.startswith("catalog:"))
async def view_catalog(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    category, type_id = await get_category(int(callback.data.split(":")[1]))

    category_data = await ItemService.get_all_categories_with_active_items(type_id)
    await state.update_data(category=category, type_id=type_id)

    keyboard = await catalog_kb.get_catalog_keyboard(category_data, type_id)

    await callback.message.edit_text(
        f"<b>🔍 {category} — Выбор по диаметру</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"Здесь вы можете выбрать нужный размер и посмотреть актуальные товары в наличии.\n\n"
        f"👇 Нажмите на подходящий диаметр ниже:",
        parse_mode='HTML',
        reply_markup=keyboard
    )


@user_router.callback_query(F.data.startswith("category:"))
async def handle_category_by_id(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    parts = callback.data.split(":")
    category_id = int(parts[1])
    page = 1
    if len(parts) == 4 and parts[2] == "page":
        page = int(parts[3])

    items = await ItemService.get_items_by_category(category_id, "active")
    data = await state.get_data()
    category = data.get("category")
    type_id = data.get("type_id")

    keyboard = await catalog_kb.get_item_keyboard(items, category_id, type_id, page=page)

    await callback.message.edit_text(
        text=(
            f"<b>🔍 {category} — Выбор по бренду</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"Предоставляем актуальный ассортимент\n\n"
            f"👇 Нажмите на подходящий бренд ниже:"
        ),
        parse_mode='HTML',
        reply_markup=keyboard
    )


@user_router.callback_query(F.data.startswith("item:"))
async def show_item_card(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    item_id = int(callback.data.split(":")[1])

    item = await ItemService.get_item_by_id(item_id)
    if not item:
        await callback.message.answer("❌ Товар не найден")
        return

    price = item.meta_data.get("price", "Цена не указана")
    description = item.meta_data.get("description", "Описание отсутствует")
    photos = item.meta_data.get("photos", [])
    season = item.meta_data.get("season")
    params = item.meta_data.get("params", "Не указаны")
    amount = item.meta_data.get("amount", "Не указано")

    season_emoji = {
        "summer": "☀️",
        "winter": "❄️",
        "allseason": "🌦️"
    }.get(season, "")

    caption = (
        f"<b>{season_emoji} {item.value}</b>\n\n"
        f"🔧 <b>Параметры:</b> {params}\n\n"
        f"📝 <b>Описание:</b>\n{description or '— отсутствует'}\n\n"
        f"📦 <b>Количество:</b> {amount} шт.\n\n"
        f"💰 <b>Цена:</b> {price} ₽\n\n"
        f"📍 <b>Для покупки обращайтесь к нам — всегда рады помочь!</b>\n"
        f"☎️ Контакты и подробности — в меню"
    )

    media = MediaGroupBuilder()
    for i, photo_id in enumerate(photos):
        if i == 0:
            media.add_photo(media=photo_id, caption=caption, parse_mode='HTML')
        else:
            media.add_photo(media=photo_id)
    await callback.message.answer_media_group(media.build())

    user = await rq.get_user_by_tg_id(callback.from_user.id)
    user_role = user.role if user else "Пользователь"

    if user_role != "Пользователь":
        keyboard = await catalog_kb.employee_item_card_keyboard(item_id)
        await callback.message.answer("Выберите действие:", reply_markup=keyboard)


@user_router.callback_query(F.data == "ignore")
async def ignore_handler(callback: CallbackQuery):
    await callback.answer()
