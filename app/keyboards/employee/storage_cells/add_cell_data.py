from datetime import datetime

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from ...general import generate_simple_keyboard, delete_message_keyboard


# Выбор типа хранения
storage_type_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Шины", callback_data="storage_type:Шины")],
    [InlineKeyboardButton(text="Шины с дисками", callback_data="storage_type:Шины с дисками")]
])

cell_data_complete_photo_report = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Готово", callback_data="storage_cells:complete_photo_report")]
])


async def generate_month_keyboard(current_year: int) -> InlineKeyboardMarkup:
    """Генерация клавиатуры с месяцами"""
    months = [
        "Январь", "Февраль", "Март",
        "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь",
        "Октябрь", "Ноябрь", "Декабрь"
    ]

    keyboard = []
    now = datetime.now()
    current_month = now.month

    # Создаём 4 ряда по 3 месяца
    for row in range(4):
        row_buttons = []
        for col in range(3):
            month_num = row * 3 + col + 1
            month_name = months[month_num - 1]

            # Выделяем текущий месяц
            if month_num == current_month and current_year == now.year:
                button_text = f"🔸 {month_name}"
            else:
                button_text = month_name

            callback_data = f"storage_month:{current_year}:{month_num}"
            row_buttons.append(InlineKeyboardButton(text=button_text, callback_data=callback_data))
        keyboard.append(row_buttons)

    # Добавляем навигацию по годам
    year_buttons = [
        InlineKeyboardButton(text="⬅️", callback_data=f"storage_year:{current_year - 1}"),
        InlineKeyboardButton(text=str(current_year), callback_data="ignore"),
        InlineKeyboardButton(text="➡️", callback_data=f"storage_year:{current_year + 1}")
    ]
    keyboard.append(year_buttons)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)