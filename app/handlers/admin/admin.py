from aiogram import F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from app.handlers.main import admin_router
import app.keyboards.admin.admin as kb
import app.database.admin_requests as rq
import app.database.requests as common_rq


@admin_router.message(Command("admin"))
async def cmd_job(message: Message):
    await message.answer(
        "<b>Вы перешли в меню администратора</b>\n\n"
        "📌 Все взаимодействия будут происходить через кнопки ниже.",
        parse_mode='HTML',
        reply_markup=kb.main_menu
    )


@admin_router.callback_query(F.data == 'back_to_main')
async def back_to_main(callback: CallbackQuery):
    await callback.answer()

    await callback.message.edit_text(
        "<b>Вы перешли в меню администратора</b>\n\n"
        "📌 Все взаимодействия будут происходить через кнопки ниже.",
        parse_mode='HTML',
        reply_markup=kb.main_menu
    )


@admin_router.callback_query(F.data == 'statistics')
async def statistics(callback: CallbackQuery):
    await callback.answer()

    stats = await rq.get_statistics(period="all")

    await callback.message.edit_text(
        f"<b>📊 Статистика бота за {stats['period_label']}:</b>\n\n"
        f"👥 <b>Общее число пользователей:</b> {stats['total_users']}\n"
        f"💰 <b>Общая сумма покупок:</b> {stats['total_amount']} ₽\n"
        f"🎁 <b>Общая сумма выданных бонусов:</b> {stats['total_bonus_amount']} ₽\n"
        f"🔄 <b>Общее количество транзакций:</b> {stats['total_transactions']}\n"
        f"📈 <b>Средняя сумма покупки:</b> {stats['average_purchase_amount']:.2f} ₽\n"
        f"🟢 <b>Количество активных пользователей:</b> {stats['active_users']}\n"
        f"💳 <b>Общая сумма бонусов на балансах:</b> {stats['total_bonus_balance']} ₽",
        parse_mode="HTML",
        reply_markup=kb.time_period
    )


@admin_router.callback_query(F.data.startswith("statistics:"))
async def handle_statistics_period(callback: CallbackQuery):
    await callback.answer()

    period = callback.data.split(":")[1]

    stats = await rq.get_statistics(period=period)

    await callback.message.edit_text(
        f"<b>📊 Статистика бота за {stats['period_label']}:</b>\n\n"
        f"👥 <b>Общее число пользователей:</b> {stats['total_users']}\n"
        f"💰 <b>Общая сумма покупок:</b> {stats['total_amount']} ₽\n"
        f"🎁 <b>Общая сумма выданных бонусов:</b> {stats['total_bonus_amount']} ₽\n"
        f"🔄 <b>Общее количество транзакций:</b> {stats['total_transactions']}\n"
        f"📈 <b>Средняя сумма покупки:</b> {stats['average_purchase_amount']:.2f} ₽\n"
        f"🟢 <b>Количество активных пользователей:</b> {stats['active_users']}\n"
        f"💳 <b>Общая сумма бонусов на балансах:</b> {stats['total_bonus_balance']} ₽",
        parse_mode="HTML",
        reply_markup=kb.time_period
    )


@admin_router.callback_query(F.data == 'bonus_system')
async def bonus_system(callback: CallbackQuery):
    await callback.answer()

    settings = await common_rq.get_bonus_system_settings()

    await callback.message.edit_text(
        "<b>💎 Общая информация о бонусной системе</b>\n\n"
        f"🔹 <b>Текущий кэшбек с покупок:</b> {settings['cashback']}%\n"
        f"🔹 <b>Максимальное списание с покупки:</b> {settings['max_debit']}%",
        parse_mode='HTML',
        reply_markup=kb.bonus_system
    )


@admin_router.callback_query(F.data == 'interact_with_user_bonus')
async def interact_with_users_bonus(callback: CallbackQuery):
    await callback.answer()

    await callback.message.edit_text(
        "Вы перешли в раздел взаимодействия с бонусами пользователей\n"
        "Воспользуйтесь меню ниже для управления:",
        parse_mode='HTML',
        reply_markup=kb.users_balance
    )


@admin_router.callback_query(F.data.startswith("bonus_users:"))
async def employee_list(callback: CallbackQuery):
    await callback.answer()

    _, balance = callback.data.split(":")



@admin_router.callback_query(F.data == "employees")
async def employee_list(callback: CallbackQuery):
    await callback.answer()

    await callback.message.edit_text(
        "<b>👥 Меню управления персоналом</b>\n\n"
        "📌 Используйте кнопки ниже для управления.",
        parse_mode='HTML',
        reply_markup=kb.manage_workers
    )


@admin_router.callback_query(F.data == "personal")
async def employee_list(callback: CallbackQuery):
    await callback.answer()

    await callback.message.edit_text(
        "<b>📋 Выберите список для просмотра:</b>\n\n",
        parse_mode="HTML",
        reply_markup=kb.view_personal_type
    )

@admin_router.callback_query(F.data.startswith("personal_list:"))
async def employee_list(callback: CallbackQuery):
    await callback.answer()

    personal_type = callback.data.split(":")[1]

    admin_dict, employee_dict = await rq.get_admin_and_employees_names()

    if personal_type == 'worker':
        personal_type = "<b>👷‍♂️ Отображаю список работников:</b>"
        keyboard = await kb.inline_personal(employee_dict)
    else:
        personal_type = "<b>👑 Отображаю список администраторов:</b>"
        keyboard = await kb.inline_personal(admin_dict)

    await callback.message.edit_text(personal_type, parse_mode='HTML', reply_markup=keyboard)


@admin_router.callback_query(F.data.startswith("employee_profile:"))
async def view_employee_profile(callback: CallbackQuery):
    await callback.answer()

    parts = callback.data.split(":")

    if len(parts) == 3:
        user_id, period = parts[1], parts[2]
    else:
        user_id, period = parts[1], "all"

    stats = await rq.get_worker_statistics(user_id, period)

    if not stats:
        await callback.message.answer("Работник не найден.")
        return

    keyboard = await kb.employee_stats(user_id)

    await callback.message.edit_text(
        f"<b>👤 Профиль работника</b>\n\n"
        f"📌 <b>Имя:</b> {stats['name']}\n"
        f"🆔 <b>User ID:</b> {stats['user_id']}\n"
        f"📅 <b>Дата выдачи роли:</b> {stats['role_assigned_date']}\n\n"
        f"<b>📊 Статистика ({stats['period_label']})</b>\n"
        f"🔹 <b>Всего транзакций:</b> {stats['total_transactions']}\n"
        f"💰 <b>Общая сумма:</b> {stats['total_amount']}\n"
        f"➕ <b>Сумма пополнений:</b> {stats['total_add']}\n"
        f"➖ <b>Сумма списаний:</b> {stats['total_remove']}",
        parse_mode="HTML",
        reply_markup=keyboard
    )
