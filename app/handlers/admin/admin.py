import os
import re
from datetime import datetime
import pandas as pd
from aiogram.fsm.context import FSMContext
from openpyxl.styles import Font
from aiogram import F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.exceptions import TelegramBadRequest
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
        f"<b>📊 Общая статистика бота</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 <b>Число пользователей:</b> {stats['total_users']}\n\n"
        f"💳 <b>Сумма бонусов на балансах:</b> {stats['total_bonus_balance']} ₽\n\n\n"
        f"<b>📊 Статистика бота {stats['period_label']}:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 <b>Сумма покупок:</b> {stats['total_amount']} ₽\n\n"
        f"🎁 <b>Сумма выданных бонусов:</b> {stats['total_bonus_amount']} ₽\n\n"
        f"🟢 <b>Количество пользователей с транзакциями:</b> {stats['active_users']}\n\n"
        f"🔄 <b>Количество транзакций:</b> {stats['total_transactions']}\n\n",
        parse_mode="HTML",
        reply_markup=kb.time_period
    )


@admin_router.callback_query(F.data.startswith("statistics:"))
async def handle_statistics_period(callback: CallbackQuery):
    await callback.answer()

    period = callback.data.split(":")[1]

    stats = await rq.get_statistics(period=period)

    try:
        await callback.message.edit_text(
            f"<b>📊 Общая статистика бота</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👥 <b>Число пользователей:</b> {stats['total_users']}\n\n"
            f"💳 <b>Сумма бонусов на балансах:</b> {stats['total_bonus_balance']} ₽\n\n\n"
            f"<b>📊 Статистика бота {stats['period_label']}:</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💰 <b>Сумма покупок:</b> {stats['total_amount']} ₽\n\n"
            f"🎁 <b>Сумма выданных бонусов:</b> {stats['total_bonus_amount']} ₽\n\n"
            f"🟢 <b>Количество пользователей с транзакциями:</b> {stats['active_users']}\n\n"
            f"🔄 <b>Количество транзакций:</b> {stats['total_transactions']}\n\n",
            parse_mode="HTML",
            reply_markup=kb.time_period
        )
    except TelegramBadRequest as e:
        # Игнорируем ошибку, если сообщение не изменилось
        if "message is not modified" not in str(e).lower():
            raise

async def clean_name(name):
    cleaned = re.sub(r'[\d+]', '', name)
    cleaned = re.sub(r'[\.\s]+', ' ', cleaned)
    return cleaned.strip()


@admin_router.callback_query(F.data == 'getAllUser')
async def get_users_to_txt(callback: CallbackQuery):
    await callback.answer()

    try:
        users = await rq.get_all_users_to_txt()

        data = {
            'Номер': range(1, len(users) + 1),
            'Дата регистрации': [user.registration_date.strftime('%d.%m.%Y %H:%M') for user in users],
            'Имя': [await clean_name(user.name) for user in users],
            'Номер телефона': [user.mobile_phone if user.mobile_phone else "не указан" for user in users],
            'Telegram ID': [user.user_id for user in users],
            'Баланс': [round(float(user.balance), 2) if user.balance is not None else 0.0 for user in users]
        }
        df = pd.DataFrame(data)

        filename = f"Пользователи_{datetime.now().strftime('%d_%m_%Y')}.xlsx"

        writer = pd.ExcelWriter(filename, engine='openpyxl')
        df.to_excel(writer, index=False, sheet_name='Пользователи')

        workbook = writer.book
        worksheet = writer.sheets['Пользователи']

        for cell in worksheet[1]:
            cell.font = Font(bold=True)

        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            worksheet.column_dimensions[column_letter].width = adjusted_width

        writer.close()

        document = FSInputFile(filename)
        await callback.message.answer_document(
            document=document,
            caption=f"💎 <b>Экспорт пользователей ({len(users)} записей)</b>",
            reply_markup=kb.delete_button_admin,
            parse_mode='HTML'
        )
        os.remove(filename)
    except Exception as e:
        await callback.message.answer(f"⚠️ Произошла ошибка при экспорте: {str(e)}")


@admin_router.callback_query(F.data == 'bonus_system')
async def bonus_system(callback: CallbackQuery):
    await callback.answer()

    settings = await common_rq.get_bonus_system_settings()

    await callback.message.edit_text(
        "<b>💎 Общая информация о бонусной системе</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔹 <b>Кэшбек с покупок:</b> {settings['cashback']}%\n\n"
        f"🔹 <b>Максимальное списание с покупки:</b> {settings['max_debit']}%\n\n"
        f"🔹 <b>Приветственный бонус новым пользователям:</b> {settings['start_bonus_balance']}\n\n"
        f"🔹 <b>Количество бонусов за отзыв:</b> {settings['voting_bonus']}\n\n"
        f"🔹 <b>Кэшбек VIP клиентам:</b> {settings['vip_cashback']}%",
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

@admin_router.callback_query(F.data == 'controlPromotions')
async def show_control_promotions(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    promotions = await common_rq.get_all_promotions()
    await state.update_data(promotions_dict=promotions)
    keyboard = await kb.generate_control_promotions_keyboard(promotions, page=1)

    await callback.message.edit_text(
    "<b>Список акций</b> 🏷️\nВыберите акцию для управления:",
        parse_mode="HTML",
        reply_markup=keyboard
    )

@admin_router.callback_query(F.data.startswith('controlPromotionsWithPage'))
async def show_control_promotions_with_page(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    page = int(callback.data.split(":")[1])
    data = await state.get_data()

    promotions = data.get("promotions_dict", {})

    keyboard = await kb.generate_control_promotions_keyboard(promotions, page=page)

    await callback.message.edit_reply_markup(reply_markup=keyboard)

@admin_router.callback_query(F.data == 'controlPromotionsBack')
async def show_control_promotions(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.delete()

    promotions = await common_rq.get_all_promotions()
    await state.update_data(promotions_dict=promotions)
    keyboard = await kb.generate_control_promotions_keyboard(promotions, page=1)

    await callback.message.answer(
    "<b>Список акций</b> 🏷️\nВыберите акцию для управления:",
        parse_mode="HTML",
        reply_markup=keyboard
    )