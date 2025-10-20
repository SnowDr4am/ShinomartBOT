from aiogram import F
from aiogram.types import Message, CallbackQuery
from app.handlers.main import admin_router
import app.database.admin_requests as rq
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.handlers.admin.admin import back_to_main, cmd_job
from config import OWNER
import app.keyboards.admin.admin as kb
from datetime import datetime


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
    user_id, period = parts[1], parts[2] if len(parts) == 3 else "all"

    stats = await rq.get_worker_statistics(user_id, period)
    if not stats:
        await callback.message.answer("Работник не найден.")
        return

    avg_rating = await rq.get_worker_average_rating(user_id)
    avg_rating_text = f"{avg_rating}" if avg_rating is not None else "Нет отзывов"

    role_date = stats['role_assigned_date']
    if isinstance(role_date, datetime):
        role_date_str = role_date.strftime("%d.%m.%Y %H:%M")
    else:
        role_date_str = "Неизвестно"

    keyboard = await kb.employee_stats(user_id)

    await callback.message.edit_text(
        f"<b>👤 Профиль работника</b>\n\n"
        f"📌 <b>Имя:</b> <a href='tg://user?id={stats['user_id']}'>{stats['name']}</a>\n"
        f"🆔 <b>User ID:</b> {stats['user_id']}\n"
        f"📅 <b>Дата выдачи роли:</b> {role_date_str}\n"
        f"📊 <b>Количество оценок:</b> {stats.get('total_ratings', 0)}\n"  # Добавлено количество оценок
        f"⭐ <b>Средняя оценка:</b> {avg_rating_text}\n\n"
        f"<b>📈 Статистика ({stats['period_label']})</b>\n"
        f"🔹 <b>Всего транзакций:</b> {stats['total_transactions']}\n"
        f"💰 <b>Общая сумма:</b> {stats['total_amount']}\n"
        f"➕ <b>Сумма зачисления бонусов:</b> {stats['total_add']}\n"
        f"➖ <b>Сумма списаний бонусов:</b> {stats['total_remove']}",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@admin_router.callback_query(F.data.startswith("worker_reviews:"))
async def view_worker_reviews(callback: CallbackQuery):
    await callback.answer()

    worker_id = callback.data.split(":")[1]
    reviews = await rq.get_worker_reviews(worker_id)

    if not reviews:
        await callback.message.answer("Отзывов за последние 30 дней нет.", reply_markup=kb.delete_button_admin)
        return

    text = "<b>📝 Отзывы за последние 30 дней</b>\n\n"
    for review in reviews:
        review_date = review['review_date'].strftime("%d.%m.%Y %H:%M")
        text += (
            "————————\n"
            f"<b>Автор:</b> <a href='tg://user?id={review['user_id']}'>{review['name']}</a>\n"
            f"<b>Дата:</b> {review_date}\n"
            f"<b>Сумма:</b> {review['amount']}\n"
            f"<b>Тип:</b> {review['transaction_type']}\n"
            f"<b>Оценка:</b> {review['rating']} ★\n"
            f"<b>Комментарий:</b> {review['comment']}\n"
        )
    text += "————————"

    await callback.message.answer(text, parse_mode="HTML", reply_markup=kb.delete_button_admin)


class Personal(StatesGroup):
    role = State()
    action = State()
    waiting_for_user_id = State()

@admin_router.callback_query(F.data.startswith('action_admin:'))
async def change_setting(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    _, role, action = callback.data.split(":")

    if action == "remove":
        if role == OWNER:
            await callback.message.answer(
                "🚫 Действие запрещено!\n"
                "Вы не можете взаимодействовать с этим пользователем."
            )
            return

        success = await rq.change_user_role(role, "Пользователь")
        if success:
            await callback.message.answer(
                f"✅ Пользователь <b>{role}</b> успешно снят с должности.",
                parse_mode="HTML"
            )
            await state.clear()
            await rq.add_role_history(callback.message.from_user.id, role, "Пользователь")

            await back_to_main(callback)
            return
        else:
            await callback.message.answer(
                f"⚠️ Пользователь <b>{role}</b> не найден в базе.\n"
                "Пожалуйста, проверьте его ID.",
                parse_mode="HTML"
            )
            return

    await state.update_data(action=action, role=role)

    await callback.message.answer("✏️ Введите ID пользователя:\n\n"
                                  "💡 <i>Для отмены напишите слово '<code>отмена</code>'</i>",
                                  parse_mode='HTML')
    await state.set_state(Personal.waiting_for_user_id)


@admin_router.message(Personal.waiting_for_user_id)
async def handle_user_id_input(message: Message, state: FSMContext):
    user_input = message.text.strip()

    if 'отмена' in user_input:
        await state.clear()

        await message.answer(
            "❌ <b>Операция успешна отменена</b>",
            parse_mode='HTML'
        )

        await cmd_job(message)

        return

    data = await state.get_data()
    role = "Администратор" if data.get("role") == "admin" else "Работник"

    success = await rq.change_user_role(user_input, role)
    if success:
        await message.answer(
            f"✅ Пользователь <b>{user_input}</b> успешно получил роль <b>{role}</b>.",
            parse_mode="HTML"
        )
        await state.clear()
        await rq.add_role_history(message.from_user.id, user_input, role)

        await cmd_job(message)
    else:
        await message.answer(
            f"⚠️ Пользователь <b>{user_input}</b> не найден в базе.\n"
            "Пожалуйста, проверьте его ID.",
            parse_mode="HTML"
        )
        return