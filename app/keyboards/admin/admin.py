from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

main_menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Статистика", callback_data='statistics')],
        [InlineKeyboardButton(text="Бонусы", callback_data='bonus_system')],
        [InlineKeyboardButton(text="Работники", callback_data='employees')]
    ]
)

time_period = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="За сутки", callback_data='statistics:day'),
        InlineKeyboardButton(text="За неделю", callback_data='statistics:week')
    ],
    [
        InlineKeyboardButton(text="За месяц", callback_data='statistics:month'),
        InlineKeyboardButton(text="За всё время", callback_data="statistics:all")
    ],
    [InlineKeyboardButton(text="Назад", callback_data='back_to_main')]
])

bonus_system = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Изменить кешбек", callback_data='change:cashback')],
    [InlineKeyboardButton(text="Изменить макс. списание", callback_data='change:max_debit')],
    [InlineKeyboardButton(text="Назад", callback_data='back_to_main')]
])

manage_workers = InlineKeyboardMarkup(inline_keyboard=[
    [
      InlineKeyboardButton(text="Список персонала", callback_data='personal')
    ],
    [
        InlineKeyboardButton(text="Добавить работника", callback_data='action:worker:add'),
        InlineKeyboardButton(text="Добавить администратора", callback_data='action:admin:add')
    ],
    [InlineKeyboardButton(text="Назад", callback_data="back_to_main")]
])

view_personal_type = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="Список работников", callback_data='personal_list:worker'),
        InlineKeyboardButton(text="Список администраторов", callback_data='personal_list:admin')
    ]
])

async def inline_personal(personal_dict):
    keyboard = InlineKeyboardBuilder()
    for user_id, name in personal_dict.items():
        keyboard.row(
            InlineKeyboardButton(
                text=name,
                callback_data=f"employee_profile:{user_id}:all"
            )
        )
    keyboard.row(InlineKeyboardButton(text='Назад', callback_data='personal'))

    return keyboard.as_markup()

async def employee_stats(user_id):
    worker_profile = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Статистика за день", callback_data=f"employee_profile:{user_id}:day"),
            InlineKeyboardButton(text="Статистика за неделю", callback_data=f"employee_profile:{user_id}:week"),
        ],
        [
            InlineKeyboardButton(text="Статистика за месяц", callback_data=f"employee_profile:{user_id}:month"),
            InlineKeyboardButton(text="Статистика за всё время", callback_data=f"employee_profile:{user_id}:all"),
        ],
        [
            InlineKeyboardButton(text="Снять роль с пользователя", callback_data=f"action:{user_id}:remove")
        ],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_main")],
    ])
    return worker_profile