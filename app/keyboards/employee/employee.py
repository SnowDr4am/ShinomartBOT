from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Новая транзакция')],
        [KeyboardButton(text='Отмена')]
    ],
    resize_keyboard=True
)

async def generate_phone_numbers_keyboard(phone_numbers: list[str]) -> InlineKeyboardMarkup:
    keyboard = []
    for phone in phone_numbers:
        button = InlineKeyboardButton(text=phone, callback_data=f'select_phone:{phone}')
        keyboard.append([button])
    cancel_button = InlineKeyboardButton(text="Отмена", callback_data='cancel')
    keyboard.append([cancel_button])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


new_transaction = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='Пополнение', callback_data='action:add'),
        InlineKeyboardButton(text='Списание', callback_data='action:remove')
    ],
    [
        InlineKeyboardButton(text='Отмена', callback_data='action:cancel')
    ]
])

confirm_transaction = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Подтвердить списание', callback_data='confirm:yes')],
    [InlineKeyboardButton(text='Отмена', callback_data='confirm:no')]
])