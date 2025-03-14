from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

# Клавиатура для регистрации
registration = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='📝 Начать регистрацию', callback_data='registration')]
])

# Клавиатура для получения номера телефона
get_phone_number = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='📱 Отправить номер телефона', request_contact=True)]
    ],
    resize_keyboard=True
)

# Главное меню
main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='👤 Профиль', callback_data='profile')],
    [InlineKeyboardButton(text='💬 Связаться с поддержкой', url='https://t.me/SnowDream5')]
])

# Меню профиля
profile = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🛒 История покупок', callback_data='history_purchase')],
    [InlineKeyboardButton(text='🔙 Назад', callback_data='main_menu')],
])


delete_button_user = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="❌ Удалить сообщение", callback_data='delete_button_user')]
])
