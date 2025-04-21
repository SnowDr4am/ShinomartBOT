from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

# Главное меню
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='💳 Новая транзакция')],
        [KeyboardButton(text='❌ Отмена')]
    ],
    resize_keyboard=True
)

# Генерация клавиатуры с номерами телефонов
async def generate_phone_numbers_keyboard(phone_numbers: list[str]) -> InlineKeyboardMarkup:
    keyboard = []
    for phone in phone_numbers:
        button = InlineKeyboardButton(text=phone, callback_data=f'select_phone:{phone}')
        keyboard.append([button])
    cancel_button = InlineKeyboardButton(text="❌ Отмена", callback_data='cancel')
    keyboard.append([cancel_button])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Генерация клавиатуры с номерами телефонов для удаления записи
async def generate_phone_numbers_appointment(phone_numbers: list[str]) -> InlineKeyboardMarkup:
    if not phone_numbers or not isinstance(phone_numbers, list):
        return InlineKeyboardMarkup(inline_keyboard=[])

    keyboard = []
    for phone in phone_numbers:
        button = InlineKeyboardButton(text=f"📞 {phone}", callback_data=f"appointment_phone:{phone}")
        keyboard.append([button])
    cancel_button = InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    keyboard.append([cancel_button])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def approved_remove_appointment_keyboard(user_id: str) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🗑️ Отменить запись",
                callback_data=f"remove_appointment_approved:{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="↩️ Назад",
                callback_data="cancel"
            )
        ]
    ])
    return keyboard

# Клавиатура для нового транзакции
async def transaction_profile_keyboard(user_id):
    new_transaction = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='💰 Пополнение', callback_data='transaction:add'),
            InlineKeyboardButton(text='💸 Списание', callback_data='transaction:remove')
        ],
        [InlineKeyboardButton(text='🛒 История покупок', callback_data=f'history_purchase_user:{user_id}')],
        [
            InlineKeyboardButton(text='❌ Отмена', callback_data='transaction:cancel')
        ]
    ])
    return new_transaction

# Клавиатура для подтверждения транзакции
confirm_transaction = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅ Подтвердить списание', callback_data='confirm:yes')],
    [InlineKeyboardButton(text='💳 Копить баллы', callback_data='confirm:no')],
    [InlineKeyboardButton(text='❌ Отмена', callback_data='confirm:cancel')]
])

assessment = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='⭐ Поставить оценку работнику ⭐', callback_data='start_assessment')]
])