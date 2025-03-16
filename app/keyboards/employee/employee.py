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

# Клавиатура для нового транзакции
new_transaction = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='💰 Пополнение', callback_data='transaction:add'),
        InlineKeyboardButton(text='💸 Списание', callback_data='transaction:remove')
    ],
    [
        InlineKeyboardButton(text='❌ Отмена', callback_data='transaction:cancel')
    ]
])

# Клавиатура для подтверждения транзакции
confirm_transaction = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅ Подтвердить списание', callback_data='confirm:yes')],
    [InlineKeyboardButton(text='💳 Копить баллы', callback_data='confirm:no')],
    [InlineKeyboardButton(text='❌ Отмена', callback_data='confirm:cancel')]
])

assessment = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Поставить оценку работнику', callback_data='start_assessment')]
])