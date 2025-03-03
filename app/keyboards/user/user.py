from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


registration = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Начать регистрацию', callback_data='registration')],
    [InlineKeyboardButton(text='Я уже зарегистрирован', callback_data='authorization')]
])

get_phone_number = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Отправить номер телефона', request_contact=True)]
    ],
    resize_keyboard=True
)

get_birthday = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Отправить дату рождения', request_contact=True)]
    ],
    resize_keyboard=True
)