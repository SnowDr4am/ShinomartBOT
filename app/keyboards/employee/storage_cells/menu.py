from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


storage_main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📦 Открыть ячейки", callback_data="storage_open_cells")],
    [InlineKeyboardButton(text="➕ Добавить ячейки", callback_data="storage_add_cells")]
])
