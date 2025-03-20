from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.handlers.main import user_router
import app.keyboards.user.user as kb
import app.database.requests as rq


class ReviewState(StatesGroup):
    waiting_for_rating = State()
    waiting_for_comment_choice = State()
    waiting_for_comment = State()


@user_router.callback_query(F.data == "start_assessment")
async def start_assessment(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = str(callback.from_user.id)
    last_transaction = await rq.get_last_transaction(user_id)

    if not last_transaction:
        await callback.message.answer(
            "<b>⚠️ У вас нет транзакций для оценки</b>",
            parse_mode="HTML"
        )
        return

    if await rq.check_review_exists(last_transaction.id):
        await callback.message.answer(
            "<b>✅ Вы уже оставили отзыв на последнюю транзакцию</b>",
            parse_mode="HTML"
        )
        return

    await callback.message.answer(
        "<b>🌟 Оцените работу мастера</b>\nПо шкале от 1 до 5:",
        reply_markup=kb.rating,
        parse_mode="HTML"
    )
    await state.update_data(last_transaction=last_transaction)
    await state.set_state(ReviewState.waiting_for_rating)


@user_router.callback_query(F.data.startswith("rate_"), ReviewState.waiting_for_rating)
async def process_rating(callback: CallbackQuery, state: FSMContext):
    rating_value = int(callback.data.split("_")[1])
    await state.update_data(rating=rating_value)
    await callback.message.edit_text(
        f"<b>⭐ Вы поставили оценку: {rating_value}</b>\nХотите оставить комментарий?",
        reply_markup=kb.comment_choice,
        parse_mode="HTML"
    )
    await state.set_state(ReviewState.waiting_for_comment_choice)
    await callback.answer()


@user_router.callback_query(F.data.startswith("comment_"), ReviewState.waiting_for_comment_choice)
async def process_comment_choice(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.split("_")[1]

    if choice == "no":
        data = await state.get_data()
        last_transaction = data["last_transaction"]
        await rq.save_review(
            user_id=str(callback.from_user.id),
            purchase_id=last_transaction.id,
            worker_id=last_transaction.worker_id,
            rating=data["rating"],
            comment=None
        )
        await callback.message.edit_text(
            "<b>🙏 Спасибо за вашу оценку!</b>",
            parse_mode="HTML"
        )
        await state.clear()
    elif choice == "yes":
        await callback.message.edit_text(
            "<b>✍️ Напишите ваш комментарий</b>\nПожалуйста, отправьте его в следующем сообщении или напишите <code>отмена</code> для отмены.",
            parse_mode="HTML"
        )
        await state.set_state(ReviewState.waiting_for_comment)
    await callback.answer()


@user_router.message(ReviewState.waiting_for_comment)
async def process_comment(message: Message, state: FSMContext):
    comment = message.text.strip()
    data = await state.get_data()
    last_transaction = data["last_transaction"]

    if comment.lower() == "отмена":
        await rq.save_review(
            user_id=str(message.from_user.id),
            purchase_id=last_transaction.id,
            worker_id=last_transaction.worker_id,
            rating=data["rating"],
            comment=None
        )
        await message.answer(
            "<b>❌ Комментарий отменён</b>\nСпасибо за оценку! 🙌",
            parse_mode="HTML"
        )
    else:
        await rq.save_review(
            user_id=str(message.from_user.id),
            purchase_id=last_transaction.id,
            worker_id=last_transaction.worker_id,
            rating=data["rating"],
            comment=comment
        )
        await message.answer(
            "<b>🌟 Спасибо за ваш отзыв!</b>",
            parse_mode="HTML"
        )
    await state.clear()