from aiogram import F
from aiogram.types import CallbackQuery

from app.handlers.main import admin_router
import app.database.ItemService as ItemService
import app.keyboards.admin.catalog as catalog_kb
from aiogram.utils.media_group import MediaGroupBuilder


@admin_router.callback_query(F.data.startswith("admin_used:"))
async def handle_admin_used(callback: CallbackQuery):
    type_ = callback.data.split(":")[1]
    title = "🛞 Выберите раздел резины" if type_ == 'tires' else "⚙️ Выберите раздел дисков"
    await callback.message.edit_text(
        title,
        reply_markup=catalog_kb.used_goods_submenu_keyboard(type_)
    )


@admin_router.callback_query(F.data.startswith("used_items:"))
async def show_used_items(callback: CallbackQuery):
    await callback.answer()
    _, type_, status = callback.data.split(":")

    type_id = 1 if type_=='tires' else 2

    items = await ItemService.get_items_by_category(type_id, status)

    if not items:
        await callback.message.edit_text("🔍 Ничего не найдено по заданному фильтру.")
        return

    title_map = {
        "active": "🟢 В продаже",
        "sold": "✅ Продано",
        "tires": "Б/У Резина",
        "discs": "Б/У Диски"
    }

    title = (
        f"Раздел: {title_map.get(type_, '')}\n\n"
        f"Статус: {title_map.get(status, '')}"
    )

    keyboard = catalog_kb.get_admin_items_keyboard(items, status, type_)
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

    season_emoji = {
        "summer": "☀️",
        "winter": "❄️",
        "allseason": "🌦️"
    }.get(season, "")

    caption = (
        f"<b>{season_emoji} {item.value}</b>\n\n"
        f"<b>Описание:</b>\n{description or '— отсутствует'}\n\n"
        f"💰 <b>Цена продажи:</b> {price} ₽\n\n"
        f"👤 <b>Продал:</b> {worker}\n\n"
        f"📅 <b>Дата продажи:</b> {sold_date}\n"
    )

    media = MediaGroupBuilder()
    for i, photo_id in enumerate(photos):
        if i == 0:
            media.add_photo(media=photo_id, caption=caption, parse_mode='HTML')
        else:
            media.add_photo(media=photo_id)
    await callback.message.answer_media_group(media.build())