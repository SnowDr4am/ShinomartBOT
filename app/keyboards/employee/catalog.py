from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

import math
from typing import List

from app.database.models import Category, Item

employee_item_type_view = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Б/У Резина', callback_data='create_item:tires')],
    [InlineKeyboardButton(text='Б/У Диски', callback_data='create_item:discs')]
])

employee_season_view = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="☀️ Летняя", callback_data='create_item_season:summer')],
    [InlineKeyboardButton(text="❄️ Зимняя", callback_data='create_item_season:winter')],
    [InlineKeyboardButton(text="🌦 Всесезон", callback_data='create_item_season:allseason')],
])

async def get_create_radius_keyboard(categories: List[Category], type_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for cat in sorted(categories, key=lambda c: c.value):
        builder.button(text=cat.value, callback_data=f"create_radius:{type_id}:{cat.id}")
    builder.adjust(2)

    return builder.as_markup()

success_upload_picture = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Готово")]
    ],
    resize_keyboard=True
)

async def confirm_employee_submission_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Сохранить", callback_data="create_confirm:yes"),
                InlineKeyboardButton(text="❌ Отменить", callback_data="create_confirm:no"),
            ]
        ]
    )


async def employee_edit_card_keyboard(item_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить название", callback_data=f"edit_card_field:{item_id}:value")],
        [InlineKeyboardButton(text="📝 Изменить описание", callback_data=f"edit_card_field:{item_id}:description")],
        [InlineKeyboardButton(text="💰 Изменить цену", callback_data=f"edit_card_field:{item_id}:price")],
        [InlineKeyboardButton(text="📸 Изменить фото", callback_data=f"edit_card_field:{item_id}:photos")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"item:{item_id}")]
    ])

async def view_update_card(item_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отобразить карточку", callback_data=f"item:{item_id}")]
    ])