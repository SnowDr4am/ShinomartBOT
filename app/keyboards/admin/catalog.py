from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import math


def used_goods_submenu_keyboard(type_: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ В продаже", callback_data=f"used_items:{type_}:active")],
        [InlineKeyboardButton(text="❌ Продано", callback_data=f"used_items:{type_}:sold")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data='back_to_main')
        ]
    ])


def get_admin_items_keyboard(items: list, status: str, type_: int, page: int = 1, page_size: int = 10) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    total_items = len(items)
    total_pages = max(1, math.ceil(total_items / page_size))
    page = max(1, min(page, total_pages))

    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end]

    if status == 'active':
        for item in page_items:
            builder.button(
                text=item.value if hasattr(item, 'value') else item['value'],
                callback_data=f"item:{item.id}"
            )
    else:
        for item in page_items:
            builder.button(
                text=item.value if hasattr(item, 'value') else item['value'],
                callback_data=f"admin_item_history:{item.id}"
            )

    builder.adjust(1)

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"items:page:{page - 1}"))
    nav_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="ignore"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"items:page:{page + 1}"))

    builder.row(*nav_buttons)
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data=f"admin_used:{type_}")
    )

    return builder.as_markup()

back_to_admin_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔙 Назад', callback_data="back_to_main")]
])