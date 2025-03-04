from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


registration = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Начать регистрацию', callback_data='registration')]
])

get_phone_number = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Отправить номер телефона', request_contact=True)]
    ],
    resize_keyboard=True
)

main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Начать регистрацию', callback_data='registration')]
])
