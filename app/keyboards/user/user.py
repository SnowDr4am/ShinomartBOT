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
    [InlineKeyboardButton(text='🛞 Срочный выкуп шин', callback_data='catalog:1')],
    [InlineKeyboardButton(text='🔥 Акции', callback_data='showPromotions')],
    [InlineKeyboardButton(text='📖 Книга жалоб и предложений', callback_data='feedback')],
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

async def admin_voting_approval_keyboard(user_id):
    approved_voting = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='✅ Подтвердить', callback_data=f"approvedVoting:{user_id}:yes"),
                InlineKeyboardButton(text='❌ Отказать', callback_data=f"approvedVoting:{user_id}:no")
            ]
        ]
    )
    return approved_voting

async def admin_voting_comment(user_id):
    comment_voting = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='✅ Да', callback_data=f"commentVoting:{user_id}:yes"),
                InlineKeyboardButton(text='❌ Нет', callback_data=f"commentVoting:{user_id}:no")
            ]
        ]
    )
    return comment_voting

async def generage_promotions_keyboard(promotion_dict, page: int = 1) -> InlineKeyboardMarkup:
    keyboard = []
    promotions_per_page = 5

    active_promotions = [
        (promo_id, promo_data) for promo_id, promo_data in promotion_dict.items()
        if promo_data.get('is_active', False)
    ]
    total_promotions = len(active_promotions)
    total_pages = (total_promotions + promotions_per_page - 1) // promotions_per_page

    if total_promotions == 0:
        keyboard.append([InlineKeyboardButton(text="Нет доступных акций", callback_data="none")])
    else:
        start = (page - 1) * promotions_per_page
        end = start + promotions_per_page
        promotions_on_page = active_promotions[start:end]

        for promo_id, promo_data in promotions_on_page:
            button_text = promo_data['short_description']
            keyboard.append([InlineKeyboardButton(text=button_text, callback_data=f"viewPromotion:{promo_id}")])

        if total_pages > 1:
            pagination_buttons = []
            if page > 1:
                pagination_buttons.append(
                    InlineKeyboardButton(text="← Назад", callback_data=f"showPromotionsWithPage:{page-1}")
                )

            pagination_buttons.append(
                InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="none")
            )

            if page < total_pages:
                pagination_buttons.append(
                    InlineKeyboardButton(text="Вперед →", callback_data=f"showPromotionsWithPage:{page+1}")
                )

            keyboard.append(pagination_buttons)

    keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

back_to_all_promotions = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="← Назад", callback_data="showPromotionsBack")]
])

feedback_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📝 Оставить жалобу", callback_data='handleFeedback:complain')],
    [InlineKeyboardButton(text="💡 Оставить предложение", callback_data='handleFeedback:idea')],
    [InlineKeyboardButton(text='🔙 Назад', callback_data='main_menu')]
])

async def admin_feedback_answer(user_id):
    keyboard = []

    keyboard.append([InlineKeyboardButton(text='💬 Ответить пользователю', callback_data=f'handleAdminAnswerFeedback:{user_id}')])
    keyboard.append([InlineKeyboardButton(text='🗑️ Удалить сообщение', callback_data=f"delete_button_user")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)