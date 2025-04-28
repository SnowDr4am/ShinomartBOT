from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message
from app.handlers.main import user_router, admin_router
from app.handlers.user.user import cmd_start
import app.keyboards.user.user as kb
import app.database.requests as rq

from app.servers.config import OWNER

class FeedbackState(StatesGroup):
    waiting_answer = State()

class FeedbackAnswerState(StatesGroup):
    waiting_answer = State()

@user_router.callback_query(F.data.startswith("handleFeedback"))
async def handle_feedback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    choice = callback.data.split(":")[1]
    await state.update_data(choice=choice)
    if choice == "complain":
        await callback.message.answer(
            "<b>Нам очень жаль 😔, что вы столкнулись с неприятной ситуацией</b>\n\n"
            "Пожалуйста, расскажите, что именно вам не понравилось. Мы обязательно рассмотрим вашу жалобу 🛠️\n\n"
            "или напишите <code>отмена</code> для отмены",
            parse_mode='HTML'
        )
    else:
        await callback.message.answer(
            "<b>У вас есть предложение к нам? 💡</b>\n\n"
            "Опишите её в следующем сообщении. Мы внимательно всё прочитаем!\n\n"
            "или напишите <code>отмена</code> для отмены",
            parse_mode='HTML'
        )
    await state.set_state(FeedbackState.waiting_answer)

@user_router.message(FeedbackState.waiting_answer)
async def process_feedback(message: Message, state: FSMContext):
    if message.text.lower() == "отмена":
        await state.clear()
        await message.answer("❌ Действие успешно отменено")
        await cmd_start(message, state)
        return

    admin_chat_id = OWNER
    user_profile = await rq.get_user_profile(message.from_user.id)
    user_link = f"<a href='tg://user?id={message.from_user.id}'>{user_profile['name']}</a>"
    mobile_phone = user_profile['mobile_phone']
    keyboard = await kb.admin_feedback_answer(message.from_user.id)
    data = await state.get_data()
    await state.clear()

    if data.get("choice") == "complain":
        caption = "🔴 <b>Новая жалоба</b>"
    else:
        caption = "💡 <b>Новое предложение</b>"

    await message.bot.send_message(
        chat_id=admin_chat_id,
        text=(
            f"{caption}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>От кого:</b>\n"
            f"<b>Профиль: </b> {user_link}\n"
            f"<b>Номер телефона: </b> {mobile_phone}\n\n"
            f"<b>Текст:</b>\n"
            f"{message.text.strip()}"
        ),
        parse_mode='HTML',
        reply_markup=keyboard
    )

    await message.answer("✅ Ваше сообщение успешно зафиксировано\nСпасибо за обратную связь!")
    await cmd_start(message, state)

@admin_router.callback_query(F.data.startswith("handleAdminAnswerFeedback"))
async def start_admin_answer_feedback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    user_id=callback.data.split(":")[1]
    await callback.message.answer(
        "<b>✉️ Напишите, пожалуйста, ответ пользователю на его обращение</b>\n\n"
        "или напишите <code>отмена</code> для отмены",
        parse_mode='HTML'
    )

    await state.update_data(user_id=user_id)
    await state.set_state(FeedbackAnswerState.waiting_answer)

@admin_router.message(FeedbackAnswerState.waiting_answer)
async def handle_admin_answer_feedback(message: Message, state: FSMContext):
    if message.text.lower() == "отмена":
        await state.clear()
        await message.answer("❌ Действие успешно отменено")
        await cmd_start(message, state)
        return

    data = await state.get_data()
    user_id = data.get("user_id")
    await state.clear()

    await message.bot.send_message(
        user_id,
        "<b>📩 Привет!</b>\n"
        "Мы внимательно прочитали ваше обращение и вот наш ответ:\n\n"
        f"{message.text.strip()}",
        parse_mode='HTML'
    )

    await message.answer(
        "✅ Ваш ответ успешно доставлен пользователю.\n\n"
        "Для удобства удалите его обращение, нажав на соответствующую кнопку 🗑️"
    )