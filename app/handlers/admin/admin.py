from aiogram import F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
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


@admin_router.callback_query(F.data == "none")
async def handle_none(callback: CallbackQuery):
    await callback.answer()


@admin_router.callback_query(F.data == 'statistics')
async def statistics(callback: CallbackQuery):
    await callback.answer()

    stats = await rq.get_statistics(period="all")

    await callback.message.edit_text(
        f"<b>📊 Статистика бота {stats['period_label']}:</b>\n\n"
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
        f"<b>📊 Статистика бота {stats['period_label']}:</b>\n\n"
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
        f"🔹 <b>Максимальное списание с покупки:</b> {settings['max_debit']}%"
        f"🔹 <b>Приветственный бонус новым пользователям:</b> {settings['start_bonus_balance']}",
        parse_mode='HTML',
        reply_markup=kb.bonus_system
    )


@admin_router.callback_query(F.data == "employees")
async def employee_list(callback: CallbackQuery):
    await callback.answer()

    await callback.message.edit_text(
        "<b>👥 Меню управления персоналом</b>\n\n"
        "📌 Используйте кнопки ниже для управления.",
        parse_mode='HTML',
        reply_markup=kb.manage_workers
    )