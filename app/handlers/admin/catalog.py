from aiogram import F
from aiogram.types import CallbackQuery

from app.handlers.main import admin_router
import app.database.ItemService as ItemService
import app.keyboards.admin.catalog as catalog_kb
from aiogram.utils.media_group import MediaGroupBuilder


@admin_router.callback_query(F.data.startswith("admin_used:"))
async def handle_admin_used(callback: CallbackQuery):
    type_ = int(callback.data.split(":")[1])
    title = "🛞 Выберите раздел резины" if type_ == 1 else "⚙️ Выберите раздел дисков"
    await callback.message.edit_text(
        title,
        reply_markup=catalog_kb.used_goods_submenu_keyboard(type_)
    )


@admin_router.callback_query(F.data.startswith("used_items:"))
async def show_used_items(callback: CallbackQuery):
    await callback.answer()
    _, type_, status = callback.data.split(":")

    type_id = int(type_)

    items = await ItemService.get_items_by_type(type_id, status)

    if not items:
        await callback.message.edit_text("🔍 Ничего не найдено по заданному фильтру", reply_markup=catalog_kb.back_to_admin_menu)
        return

    title_map = {
        "active": "🟢 В продаже",
        "sold": "✅ Продано",
        "tires": "Б/У Шины",
        "discs": "Б/У Диски"
    }

    title = (
        f"Раздел: {title_map.get(type_, '')}\n\n"
        f"Статус: {title_map.get(status, '')}"
    )

    keyboard = catalog_kb.get_admin_items_keyboard(items, status, type_id)
    await callback.message.edit_text(
        text=title,
        reply_markup=keyboard
    )


@admin_router.callback_query(F.data.startswith("admin_item_history:"))
async def view_item_history(callback: CallbackQuery):
    await callback.answer()

    item_id = int(callback.data.split(":")[1])
    item = await ItemService.get_item_by_id(item_id)

    price = item.meta_data.get("price", "Цена не указана")
    description = item.meta_data.get("description", "Описание отсутствует")
    photos = item.meta_data.get("photos", [])
    season = item.meta_data.get("season")
    worker = item.meta_data.get("worker", "неизвестно")
    sold_date = item.meta_data.get("sold_date", "дата не указана")
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
        f"📦 <b>Количество:</b> {amount} шт.\n"
        f"💰 <b>Цена продажи:</b> {price} ₽\n\n"
        f"👤 <b>Продал:</b> {worker}\n"
        f"📅 <b>Дата продажи:</b> {sold_date}"
    )

    media = MediaGroupBuilder()
    for i, photo_id in enumerate(photos):
        if i == 0:
            media.add_photo(media=photo_id, caption=caption, parse_mode='HTML')
        else:
            media.add_photo(media=photo_id)
    await callback.message.answer_media_group(media.build())