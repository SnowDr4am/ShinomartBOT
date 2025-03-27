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
    [InlineKeyboardButton(text='⚙️ Записаться в сервис', callback_data='entry_server')],
    [InlineKeyboardButton(text='💬 Связаться с нами', callback_data='contact')]
])

# Меню профиля
profile = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🎟️ Сгенерировать QR', callback_data='get_qrcode')],
    [InlineKeyboardButton(text='🛒 История покупок', callback_data='history_purchase')],
    [InlineKeyboardButton(text='🔙 Назад', callback_data='main_menu')],
])


delete_button_user = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="❌ Удалить сообщение", callback_data='delete_button_user')]
])

back_to_main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔙 Назад', callback_data='main_menu')]
])

rating = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="1", callback_data="rate_1"),
        InlineKeyboardButton(text="2", callback_data="rate_2"),
        InlineKeyboardButton(text="3", callback_data="rate_3"),
        InlineKeyboardButton(text="4", callback_data="rate_4"),
        InlineKeyboardButton(text="5", callback_data="rate_5"),
    ]
])

comment_choice = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="Да", callback_data="comment_yes"),
        InlineKeyboardButton(text="Нет", callback_data="comment_no"),
    ]
])

cancel_appointment_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="❌ Отменить запись", callback_data="appointment_delete")]
])

async def get_approved_appointment_keyboard(user_id):
    approved_appointment = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Да", callback_data=f"approved:{user_id}:yes")],
                [InlineKeyboardButton(text="❌ Отменить запись", callback_data=f"approved:{user_id}:remove")]
            ])
    return approved_appointment