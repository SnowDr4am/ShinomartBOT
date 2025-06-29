from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

import math
from typing import List

from app.database.models import Category, Item


async def get_catalog_keyboard(categories: List[Category], type_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for cat in sorted(categories, key=lambda c: c.value):
        builder.button(text=cat.value,callback_data=f"category:{cat.id}")

    builder.adjust(2)

    category = "Предложить свои Б/У шины" if type_id == 1 else "Предложить свои Б/У диски"
    builder.row(InlineKeyboardButton(text=category, callback_data=f"submit_item:{type_id}"))

    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu"))

    return builder.as_markup()


async def get_item_keyboard(
        items: List[Item],
        category_id: int,
        type_id: int,
        page: int = 1,
        page_size: int = 10
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    total_items = len(items)
    total_pages = math.ceil(total_items / page_size)
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_items = items[start_idx:end_idx]

    season_emoji_map = {
        "summer": "☀️",
        "winter": "❄️",
        "allseason": "🌦️"
    }

    for item in page_items:
        price = item.meta_data.get("price", "Цена не указана")
        season = item.meta_data.get("season", "").lower()
        emoji = season_emoji_map.get(season, "")
        text = f"{emoji} {item.value} — {price} ₽" if emoji else f"{item.value} — {price} ₽"
        builder.button(text=text, callback_data=f"item:{item.id}")

    builder.adjust(1)

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"category:{category_id}:page:{page - 1}"))
    nav_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="ignore"))

    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"category:{category_id}:page:{page + 1}"))

    builder.row(*nav_buttons)

    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=f"catalog:{type_id}"))
    return builder.as_markup()


user_season_view = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="☀️ Летняя", callback_data='submit_item_season:summer')],
    [InlineKeyboardButton(text="❄️ Зимняя", callback_data='submit_item_season:winter')],
    [InlineKeyboardButton(text="🌦 Всесезон", callback_data='submit_item_season:allseason')],
])


async def get_submit_radius_keyboard(categories: List[Category], type_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for cat in sorted(categories, key=lambda c: c.value):
        builder.button(text=cat.value, callback_data=f"submit_radius:{type_id}:{cat.id}")
    builder.adjust(2)

    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=f"catalog:{type_id}"))

    return builder.as_markup()

success_upload_picture = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Готово")]
    ],
    resize_keyboard=True
)

async def confirm_submission_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="submit_confirm:yes")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="submit_confirm:no")]
    ])

async def admin_review_submission_keyboard(telegram_user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤝 Пригласить клиента", callback_data=f"submit_admin_action:yes:{telegram_user_id}")],
        [InlineKeyboardButton(text="🚫 Отказать клиенту", callback_data=f"submit_admin_action:no:{telegram_user_id}")]
    ])

async def employee_item_card_keyboard(item_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Товар продан", callback_data=f"item_card_action:{item_id}:sold")],
        [InlineKeyboardButton(text="✏️ Отредактировать карточку", callback_data=f"item_card_action:{item_id}:edit")],
        [InlineKeyboardButton(text="❌ Удалить сообщение", callback_data="delete_button_user")]
    ])