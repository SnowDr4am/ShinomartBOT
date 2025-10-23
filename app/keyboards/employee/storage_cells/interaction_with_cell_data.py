from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from ...general import generate_simple_keyboard, delete_message_keyboard


async def generate_month_keyboard(current_year: int, cell_id: int, selected_month: int | None = None) -> InlineKeyboardMarkup:
    """Генерация клавиатуры с месяцами, выделяя выбранный и добавляя кнопку 'Назад'"""
    months = [
        "Январь", "Февраль", "Март",
        "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь",
        "Октябрь", "Ноябрь", "Декабрь"
    ]

    keyboard = []

    # 4 ряда по 3 месяца
    for row in range(4):
        row_buttons = []
        for col in range(3):
            month_num = row * 3 + col + 1
            month_name = months[month_num - 1]

            # Подсвечиваем выбранный месяц
            if selected_month == month_num:
                button_text = f"✅ {month_name}"
            else:
                button_text = month_name

            callback_data = f"storage_month:{current_year}:{month_num}"
            row_buttons.append(InlineKeyboardButton(text=button_text, callback_data=callback_data))
        keyboard.append(row_buttons)

    # Навигация по годам
    year_buttons = [
        InlineKeyboardButton(text="⬅️", callback_data=f"storage_year:{current_year - 1}"),
        InlineKeyboardButton(text=f"{current_year}", callback_data="ignore"),
        InlineKeyboardButton(text="➡️", callback_data=f"storage_year:{current_year + 1}")
    ]
    keyboard.append(year_buttons)

    # Кнопка "Назад"
    keyboard.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data=f"storage_cell:{cell_id}")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Подтверждение действий
async def get_confirmation_keyboard(action: str, cell_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения"""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"storage_confirm:{action}:{cell_id}"),
            InlineKeyboardButton(text="❌ Нет", callback_data=f"storage_cell:{cell_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
