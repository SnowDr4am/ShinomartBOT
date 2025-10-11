from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


complete_photo_report = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Готово", callback_data="close_work_day:complete_picture_report")]
])