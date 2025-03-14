from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Главное меню
main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📊 Статистика", callback_data='statistics')],
    [InlineKeyboardButton(text="💳 Бонусы", callback_data='bonus_system')],
    [InlineKeyboardButton(text="👨‍💼 Работники", callback_data='employees')]
])

# Выбор периода времени для статистики
time_period = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="📅 За сутки", callback_data='statistics:day'),
        InlineKeyboardButton(text="📅 За неделю", callback_data='statistics:week')
    ],
    [
        InlineKeyboardButton(text="📅 За месяц", callback_data='statistics:month'),
        InlineKeyboardButton(text="📅 За всё время", callback_data="statistics:all")
    ],
    [InlineKeyboardButton(text="🔙 Назад", callback_data='back_to_main')]
])

# Система бонусов
bonus_system = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="💸 Изменить кешбек", callback_data='change:cashback')],
    [InlineKeyboardButton(text="💳 Изменить макс. списание", callback_data='change:max_debit')],
    [InlineKeyboardButton(text="👥 Взаимодействие с пользователями", callback_data='interact_with_user_bonus')],
    [InlineKeyboardButton(text="🔙 Назад", callback_data='back_to_main')]
])

users_balance = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Пользователи 1000-5000", callback_data='bonus_users:1000')],
    [InlineKeyboardButton(text="Пользователи 5001-10000", callback_data='bonus_users:5000')],
    [InlineKeyboardButton(text="Пользователи 10000+", callback_data='bonus_users:10000')],
    [
        InlineKeyboardButton(text="Забрать бонусы", callback_data='bonus:add'),
        InlineKeyboardButton(text="Начислить бонусы", callback_data='bonus:remove')
    ],
    [InlineKeyboardButton(text="🔙 Назад", callback_data='back_to_main')]
])

# Управление работниками
manage_workers = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="👥 Список персонала", callback_data='personal')],
    [
        InlineKeyboardButton(text="➕ Добавить работника", callback_data='action:worker:add'),
        InlineKeyboardButton(text="➕ Добавить администратора", callback_data='action:admin:add')
    ],
    [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
])

# Выбор типа персонала (работник или администратор)
view_personal_type = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="🧑‍💼 Список работников", callback_data='personal_list:worker'),
        InlineKeyboardButton(text="👨‍💻 Список администраторов", callback_data='personal_list:admin')
    ]
])

# Динамическая клавиатура для персонала
async def inline_personal(personal_dict):
    keyboard = InlineKeyboardBuilder()
    for user_id, name in personal_dict.items():
        keyboard.row(
            InlineKeyboardButton(
                text=name,
                callback_data=f"employee_profile:{user_id}:all"
            )
        )
    keyboard.row(InlineKeyboardButton(text='🔙 Назад', callback_data='personal'))

    return keyboard.as_markup()

# Клавиатура для статистики работника
async def employee_stats(user_id):
    worker_profile = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Статистика за день", callback_data=f"employee_profile:{user_id}:day"),
            InlineKeyboardButton(text="📊 Статистика за неделю", callback_data=f"employee_profile:{user_id}:week"),
        ],
        [
            InlineKeyboardButton(text="📊 Статистика за месяц", callback_data=f"employee_profile:{user_id}:month"),
            InlineKeyboardButton(text="📊 Статистика за всё время", callback_data=f"employee_profile:{user_id}:all"),
        ],
        [
            InlineKeyboardButton(text="❌ Снять роль с пользователя", callback_data=f"action:{user_id}:remove")
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")],
    ])
    return worker_profile

# Клавиатура для отображения списка пользователей с балансом
async def create_users_keyboard(users_dict: dict, page: int = 1, users_per_page: int = 10) -> InlineKeyboardMarkup:
    """
    Создает inline-клавиатуру с пользователями и пагинацией.

    :param users_dict: Словарь с пользователями.
    :param page: Текущая страница.
    :param users_per_page: Количество пользователей на одной странице.
    :return: InlineKeyboardMarkup.
    """
    keyboard = []

    users_list = list(users_dict.items())
    total_users = len(users_list)
    total_pages = (total_users + users_per_page - 1) // users_per_page

    start = (page - 1) * users_per_page
    end = start + users_per_page
    users_on_page = users_list[start:end]

    for user_id, user_data in users_on_page:
        name = user_data["name"]
        bonus_balance = user_data["bonus-balance"]
        button_text = f"{name} {bonus_balance}"
        keyboard.append([InlineKeyboardButton(text=button_text, callback_data=f"bonus_user:{user_id}")])

    if total_pages > 1:
        pagination_buttons = []
        if page > 1:
            pagination_buttons.append(InlineKeyboardButton(text="<-", callback_data=f"page:{page - 1}"))
        pagination_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="none"))
        if page < total_pages:
            pagination_buttons.append(InlineKeyboardButton(text="->", callback_data=f"page:{page + 1}"))
        keyboard.append(pagination_buttons)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)