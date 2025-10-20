from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.handlers.main import user_router, admin_router
import app.keyboards.user.user as kb
import app.database.requests as rq

from config import OWNER

class VotingApproved(StatesGroup):
    waiting_picture = State()
    waiting_comment = State()

@user_router.callback_query(F.data == 'voting_approve')
async def start_voting_approve(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    check_vote_status = await rq.get_user_vote_history(str(callback.from_user.id))
    if check_vote_status:
        await callback.message.answer(
            "🖼️ <b>Пожалуйста, отправьте скриншот вашего отзыва</b> в следующем сообщении\n"
            "❌ Если передумали — напишите <code>отмена</code> для отмены",
            parse_mode='HTML'
        )

        await state.set_state(VotingApproved.waiting_picture)
    else:
        await callback.message.delete()
        await callback.message.answer(
            "ℹ️ <b>Вы уже оставляли отзыв</b>\n"
            "🔁 <b>Повторно это сделать не получится</b>",
            parse_mode='HTML'
        )
        return

@user_router.message(VotingApproved.waiting_picture)
async def process_picture(message: Message, state: FSMContext):
    if not message.photo:
        if message.text.lower() == 'отмена':
            await state.clear()
            await message.answer(
                "❌ <b>Вы отменили операцию.</b>\nЕсли передумаете — просто начните заново 😊",
                parse_mode='HTML'
            )
        else:
            await message.answer(
                "📸 <b>Пожалуйста, отправьте скриншот как изображение</b>, а не как файл",
                parse_mode='HTML'
            )
        return

    photo = message.photo[-1]
    admin_chat_id = OWNER
    user_profile = await rq.get_user_profile(message.from_user.id)
    user_link = f"<a href='tg://user?id={message.from_user.id}'>{user_profile['name']}</a>"
    keyboard = await kb.admin_voting_approval_keyboard(message.from_user.id)

    await message.bot.send_photo(
        chat_id=admin_chat_id,
        photo=photo.file_id,
        caption=(
            f"🆕 <b>Новый отзыв от пользователя</b> {user_link}\n"
            "🔍 <b>Пожалуйста, проверьте его</b>"
        ),
        reply_markup=keyboard,
        parse_mode='HTML'
    )

    await state.clear()
    await message.answer(
        "🕵️ <b>Ваш отзыв отправлен на модерацию</b>\n"
        "⏳ <b>Ожидайте, постараемся принять решение как можно скорее</b>",
        parse_mode='HTML'
    )

@admin_router.callback_query(F.data.startswith("approvedVoting"))
async def process_approved(callback: CallbackQuery):
    await callback.answer()

    _, user_id, confirm = callback.data.split(":")
    await callback.message.delete()

    if confirm == "yes":
        bonus_system = await rq.get_bonus_system_settings()
        await rq.set_bonus_balance(user_id, "add", bonus_system['voting_bonus'], 0, "Администратор")
        await rq.create_voting_history(user_id)
        user_link = f"<a href='tg://user?id={user_id}'> (профиль)</a>"

        await callback.message.answer(
            f"🎉 <b>Бонусы за отзыв успешно начислены пользователю {user_link}!</b>",
            parse_mode='HTML'
        )

        await callback.bot.send_message(
            chat_id=user_id,
            text=(
                "✅ <b>Ваш отзыв принят!</b>\n"
                f"💰 <b>На ваш баланс начислено {bonus_system['voting_bonus']} бонусов</b>\n\n"
                "🙏 <b>Спасибо за поддержку!</b>"
            ),
            parse_mode='HTML'
        )
    elif confirm == 'no':
        keyboard = await kb.admin_voting_comment(user_id)
        await callback.message.answer(
            "❌ <b>Вы отказали пользователю в начислении бонуса за отзыв</b>\n"
            "📝 <b>Хотите оставить комментарий?</b>",
            reply_markup=keyboard,
            parse_mode='HTML'
        )


@admin_router.callback_query(F.data.startswith("commentVoting"))
async def proccess_choice_comment(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    _, user_id, choice = callback.data.split(":")
    await callback.message.delete()
    if choice == 'yes':
        await callback.message.answer(
            "💬 <b>Напишите ваш комментарий</b>\n"
            "📩 Пожалуйста, отправьте его в следующем сообщении\n"
            "❌ Или напишите <code>отмена</code> для отмены.",
            parse_mode='HTML'
        )
        await state.update_data(user_id=user_id)
        await state.set_state(VotingApproved.waiting_comment)
    else:
        await state.clear()
        user_link = f"<a href='tg://user?id={user_id}'> (профиль)</a>"
        await callback.message.answer(
            f"⚠️ <b>Пользователю {user_link} отказано в начислении бонусов за отзыв без объяснения причин</b>",
            parse_mode='HTML'
        )
        await callback.bot.send_message(
            chat_id=user_id,
            text=(
                "❌ <b>Вам отказано в начислении бонусов за отзыв</b> без объяснения причин"
            ),
            parse_mode='HTML'
        )


@admin_router.message(VotingApproved.waiting_comment)
async def process_comment(message: Message, state: FSMContext):
    comment = message.text.strip()
    data = await state.get_data()
    await state.clear()
    user_id = data["user_id"]
    user_link = f"<a href='tg://user?id={user_id}'> (профиль)</a>"

    if comment.lower() == 'отмена':
        await message.answer(
            f"⚠️ <b>Пользователю {user_link} отказано в начислении бонусов за отзыв без объяснения причин</b>",
            parse_mode='HTML'
        )

        await message.bot.send_message(
            chat_id=data["user_id"],
            text=(
                "❌ <b>Вам отказано в начислении бонусов за отзыв</b> без объяснения причин"
            ),
            parse_mode='HTML'
        )
    else:
        await message.answer(
            f"⚠️ <b>Пользователю {user_link} отказано в начислении бонусов за отзыв</b>\n"
            f"📝 <b>Причина:</b> {comment}",
            parse_mode='HTML'
        )

        await message.bot.send_message(
            chat_id=data["user_id"],
            text=(
                "❌ <b>Вам отказано в начислении бонусов за отзыв</b>\n"
                f"📝 <b>Причина:</b> {comment}"
            ),
            parse_mode='HTML'
        )