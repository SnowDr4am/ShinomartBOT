from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultLocation
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Главное меню
main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📊 Статистика", callback_data='statistics')],
    [InlineKeyboardButton(text="💳 Бонусы", callback_data='bonus_system')],
    [InlineKeyboardButton(text="👨‍💼 Работники", callback_data='employees')],
    [InlineKeyboardButton(text="🔥 Акции", callback_data='controlPromotions')],
    [InlineKeyboardButton(text="💬 Отправить рассылку", callback_data='send_message')],
    [InlineKeyboardButton(text="🛞 Б/У Резина", callback_data='admin_used:tires')],
    [InlineKeyboardButton(text="⚙️ Б/У Диски", callback_data='admin_used:discs')],
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
    [InlineKeyboardButton(text="🔹 Выгрузить всех пользователей", callback_data='getAllUser')],
    [InlineKeyboardButton(text="◀️ Назад", callback_data='back_to_main')]
])

# Система бонусов
bonus_system = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔹 Изменить кешбэк", callback_data='change:cashback')],
    [InlineKeyboardButton(text="🔹 Изменить макс. списание", callback_data='change:max_debit')],
    [InlineKeyboardButton(text="🔹 Изменить приветственный бонус", callback_data='change:welcome_bonus')],
    [InlineKeyboardButton(text="🔹 Изменить количество бонусов за отзыв", callback_data='change:voting_bonus')],
    [InlineKeyboardButton(text="🔹 Изменить VIP кешбэк", callback_data='change:vip_cashback')],
    [InlineKeyboardButton(text="🔹 Взаимодействие с пользователями", callback_data='interact_with_user_bonus')],
    [InlineKeyboardButton(text="◀️ Назад", callback_data='back_to_main')]
])

users_balance = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="👤 Пользователи 1000–5000", callback_data='bonus_users:1000')],
    [InlineKeyboardButton(text="👥 Пользователи 5001–10000", callback_data='bonus_users:5000')],
    [InlineKeyboardButton(text="🧑 Пользователи 10000+", callback_data='bonus_users:10000')],
    [InlineKeyboardButton(text="👑 VIP клиенты", callback_data='vipClients')],
    [InlineKeyboardButton(text="🎁 Начислить/Списать бонусы", callback_data='presentBonus')],
    [InlineKeyboardButton(text="◀️ Назад", callback_data='bonus_system')]
])
# Управление работниками
manage_workers = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="👥 Список персонала", callback_data='personal')],
    [
        InlineKeyboardButton(text="➕ Добавить работника", callback_data='action_admin:worker:add'),
        InlineKeyboardButton(text="➕ Добавить администратора", callback_data='action_admin:admin:add')
    ],
    [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
])

# Выбор типа персонала (работник или администратор)
view_personal_type = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="🧑‍💼 Список работников", callback_data='personal_list:worker'),
        InlineKeyboardButton(text="👨‍💻 Список администраторов", callback_data='personal_list:admin')
    ],
    [
        InlineKeyboardButton(text="◀️ Назад", callback_data='employees')
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
    keyboard.row(InlineKeyboardButton(text='◀️ Назад', callback_data='personal'))

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
            InlineKeyboardButton(text="📝 Посмотреть отзывы", callback_data=f"worker_reviews:{user_id}"),
        ],
        [
            InlineKeyboardButton(text="❌ Снять роль с пользователя", callback_data=f"action_admin:{user_id}:remove")
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="employees")],
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

    if total_users == 0:
        keyboard.append([InlineKeyboardButton(text="Нет пользователей", callback_data="none")])
    else:
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

    keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="interact_with_user_bonus")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def get_user_profile_admin(user_id):
    user_profile = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🛒 История покупок', callback_data=f'history_purchase_user:{user_id}')],
        [
            InlineKeyboardButton(text="❌ Забрать бонусы", callback_data=f'bonus:remove:{user_id}'),
            InlineKeyboardButton(text="✅ Начислить бонусы", callback_data=f'bonus:add:{user_id}')
        ],
        [InlineKeyboardButton(text='◀️ Назад', callback_data='back_to_main')],
    ])
    return user_profile


delete_button_admin = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="❌ Удалить сообщение", callback_data='delete_button_admin')]
])

send_message_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='📝 Гайд по форматированию', callback_data='instructionHTML')],
    [InlineKeyboardButton(text='❌ Отмена', callback_data='cancelAction')]
])

confirm_button = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅ Подтвердить', callback_data='confirmSendMessage')],
    [InlineKeyboardButton(text='❌ Отмена', callback_data='cancelAction')]
])

cancel_bonus_system = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='❌ Отмена', callback_data='cancelAction')]
])

vip_clients_menu_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="👁️ Посмотреть VIP-клиентов", callback_data="viewVipClient")],
    [
        InlineKeyboardButton(text="➕ Добавить VIP-клиента", callback_data='changeVipClient:add'),
        InlineKeyboardButton(text="➖ Удалить VIP-клиента", callback_data='changeVipClient:remove'),
    ],
    [InlineKeyboardButton(text="◀️ Назад", callback_data='bonus_system')]
])

async def generate_control_promotions_keyboard(promotion_dict, page: int = 1):
    keyboard = []
    promotions_per_page = 5

    promotions_list = list(promotion_dict.items())
    total_promotions = len(promotions_list)
    total_pages = (total_promotions + promotions_per_page - 1) // promotions_per_page

    if total_promotions == 0:
        keyboard.append([InlineKeyboardButton(text="Нет доступных акций", callback_data='none')])
    else:
        start = (page - 1) * promotions_per_page
        end = start + promotions_per_page
        promotions_on_page = promotions_list[start:end]

        for promo_id, promo_data in promotions_on_page:
            status = "✅" if promo_data.get('is_active', False) else "❌"
            keyboard.append([InlineKeyboardButton(text=f"{promo_data['short_description']} {status}", callback_data=f"editPromo:{promo_id}")])

        if total_pages > 1:
            pagination_buttons = []
            if page > 1:
                pagination_buttons.append(InlineKeyboardButton(text="← Назад", callback_data=f"controlPromotionsWithPage:{page-1}"))

            pagination_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="none"))

            if page < total_pages:
                pagination_buttons.append(InlineKeyboardButton(text="Вперед →", callback_data=f"controlPromotionsWithPage:{page+1}"))

            keyboard.append(pagination_buttons)
    keyboard.append([
        InlineKeyboardButton(text="➕ Добавить акцию", callback_data="addPromotion"),
        InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

confirm_new_promotion = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Принять", callback_data="confirmNewPromotion:yes")],
    [InlineKeyboardButton(text="❌ Отклонить", callback_data="confirmNewPromotion:no")]
])

async def get_promotion_management(promo_id):
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text="✏️ Изменить полное описание", callback_data=f"promotionEdit:full_text:{promo_id}"))
    builder.row(InlineKeyboardButton(text="✏️ Изменить краткое описание", callback_data=f"promotionEdit:short_text:{promo_id}"))
    builder.row(InlineKeyboardButton(text="🖼 Изменить изображение", callback_data=f"promotionEdit:image:{promo_id}"))
    builder.row(InlineKeyboardButton(text="👁️ Скрыть/показать акцию", callback_data=f"promotionEdit:toggle:{promo_id}"))
    builder.row(InlineKeyboardButton(text="❌ Удалить акцию", callback_data=f"promotionEdit:delete:{promo_id}"))
    builder.row(InlineKeyboardButton(text="🗑️ Удалить сообщение", callback_data=f"delete_button_admin"))
    builder.row(InlineKeyboardButton(text='◀️ Назад', callback_data='controlPromotionsBack'))

    return builder.as_markup()

async def get_promotion(promo_id):
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text="Показать обновленную акцию", callback_data=f"editPromo:{promo_id}"))

    return builder.as_markup()

async def confirm_delete_promotion(promo_id):
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirmDeletePromotion:{promo_id}"))
    builder.row(InlineKeyboardButton(text="❌ Нет, отменить", callback_data=f"editPromo:{promo_id}"))

    return builder.as_markup()
