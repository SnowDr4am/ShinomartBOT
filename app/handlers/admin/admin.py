from aiogram import F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from app.handlers.main import admin_router
import app.keyboards.admin.admin as kb
import app.database.admin_requests as rq
import app.database.requests as common_rq
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

@admin_router.message(Command("admin"))
async def cmd_job(message: Message):
    await message.answer("Вы перешли в меню администратора\n"
                         "Все взаимодействия будут происходить через кнопки снизу",
                         parse_mode='HTML', reply_markup=kb.main_menu)

@admin_router.callback_query(F.data == 'back_to_main')
async def back_to_main(callback: CallbackQuery):
    await callback.answer()

    await callback.message.answer("Вы перешли в меню администратора\n"
                                "Все взаимодействия будут происходить через кнопки снизу",
        reply_markup=kb.main_menu
    )

@admin_router.callback_query(F.data == 'statistics')
async def statistics(callback: CallbackQuery):
    await callback.answer()

    stats = await rq.get_statistics(period="all")

    await callback.message.answer(
        f"Статистика бота {stats['period_label']}:\n\n"
        f"Общее число пользователей: {stats['total_users']}\n"
        f"Общая сумма покупок пользователей: {stats['total_amount']}\n"
        f"Общая сумма выданных бонусов: {stats['total_bonus_amount']}\n"
        f"Общее количество транзакций: {stats['total_transactions']}\n"
        f"Средняя сумма покупки: {stats['average_purchase_amount']:.2f}\n"
        f"Количество активных пользователей: {stats['active_users']}\n"
        f"Общая сумма бонусов на балансах: {stats['total_bonus_balance']}",
        reply_markup=kb.time_period
    )


@admin_router.callback_query(F.data.startswith("statistics:"))
async def handle_statistics_period(callback: CallbackQuery):
    await callback.answer()

    period = callback.data.split(":")[1]

    stats = await rq.get_statistics(period=period)

    await callback.message.edit_text(
        f"Статистика бота {stats['period_label']}:\n\n"
        f"Общее число пользователей: {stats['total_users']}\n"
        f"Общая сумма покупок пользователей: {stats['total_amount']}\n"
        f"Общая сумма выданных бонусов: {stats['total_bonus_amount']}\n"
        f"Общее количество транзакций: {stats['total_transactions']}\n"
        f"Средняя сумма покупки: {stats['average_purchase_amount']:.2f}\n"
        f"Количество активных пользователей: {stats['active_users']}\n"
        f"Общая сумма бонусов на балансах: {stats['total_bonus_balance']}",
        reply_markup=kb.time_period
    )


@admin_router.callback_query(F.data == 'bonus_system')
async def bonus_system(callback: CallbackQuery):
    await callback.answer()

    settings = await common_rq.get_bonus_system_settings()

    await callback.message.answer(
        f"<b>Общая информация о бонусной системе</b>\n\n"
        f"Текущий кешбек с покупок: <b>{settings['cashback']}%</b>\n"
        f"Максимальное списание с покупки: <b>{settings['max_debit']}%</b>",
        parse_mode='HTML', reply_markup=kb.bonus_system
    )


@admin_router.callback_query(F.data == "employees")
async def employee_list(callback: CallbackQuery):
    await callback.answer()

    await callback.message.answer(
        f"Вы находитесь в меню управления персоналом\n"
        f"Воспользуйтесь меню ниже для управления",
        parse_mode='HTML', reply_markup=kb.manage_workers
    )

@admin_router.callback_query(F.data == "personal")
async def employee_list(callback: CallbackQuery):
    await callback.answer()

    await callback.message.answer("Выберите какой список вы хотите посмотреть",
                                  reply_markup=kb.view_personal_type)

@admin_router.callback_query(F.data.startswith("personal_list:"))
async def employee_list(callback: CallbackQuery):
    await callback.answer()

    personal_type = callback.data.split(":")[1]

    admin_dict, employee_dict = await rq.get_admin_and_employees_names()

    if personal_type == 'worker':
        personal_type = "Отображаю список работников"
        keyboard = await kb.inline_personal(employee_dict)
    else:
        personal_type = "Отображаю список администраторов"
        keyboard = await kb.inline_personal(admin_dict)

    await callback.message.edit_text(personal_type, reply_markup=keyboard)


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

    await callback.message.answer(
        f"<b>Профиль работника:</b>\n\n"
        f"Имя: {stats['name']}\n"
        f"User ID: {stats['user_id']}\n"
        f"Дата выдачи роли: {stats['role_assigned_date']}\n\n"
        f"<b>Статистика ({stats['period_label']}):</b>\n"
        f"Всего транзакций: {stats['total_transactions']}\n"
        f"Общая сумма: {stats['total_amount']}\n"
        f"Сумма пополнений: {stats['total_add']}\n"
        f"Сумма списаний: {stats['total_remove']}",
        parse_mode='HTML', reply_markup=keyboard
    )



