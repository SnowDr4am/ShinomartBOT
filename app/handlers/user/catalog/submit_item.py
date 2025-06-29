from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram.utils.media_group import MediaGroupBuilder

from app.servers.config import TIRES_AND_DISCS_CHANNEL
from app.handlers.main import user_router, admin_router
import app.database.ItemService as ItemService
import app.database.requests as rq
import app.keyboards.user.catalog as catalog_kb
from app.utils.states import SubmitItemStates
from app.handlers.user.user import main_menu

from .utils import *


@user_router.callback_query(F.data.startswith("submit_item:"))
async def start_submit_new_item(callback: CallbackQuery):
    await callback.answer()

    type_id = int(callback.data.split(":")[1])
    category_name, _ = await get_category(type_id)

    categories = await ItemService.get_all_categories(type_id)

    keyboard = await catalog_kb.get_submit_radius_keyboard(categories, type_id)

    await callback.message.edit_text(
        f"📢 Вы начали предложение новой позиции для категории <b>{category_name}</b>\n\n"
        f"Выберите диаметр, чтобы начать:",
        parse_mode='HTML',
        reply_markup=keyboard
    )

@user_router.callback_query(F.data.startswith("submit_radius:"))
async def submit_radius_chosen(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    type_id = int(callback.data.split(":")[1])
    category_id = int(callback.data.split(":")[2])
    category_name, _ = await get_category(type_id)

    await state.update_data(category_id=category_id, type_id=type_id)

    if type_id == 1:
        await callback.message.edit_text(
            f"❄️ <b>{category_name}</b> — укажите сезон использования:\n\n"
            "Выберите один из вариантов ниже 👇",
            parse_mode='HTML',
            reply_markup=catalog_kb.user_season_view
        )
    else:
        await callback.message.edit_text(
            "🏷 <b>Введите название бренда</b>\n\n"
            "🛑 Напишите <code>отмена</code>, чтобы выйти на любом этапе.",
            parse_mode='HTML'
        )
        await state.set_state(SubmitItemStates.waiting_brand)


@user_router.callback_query(F.data.startswith("submit_item_season:"))
async def handle_tires_season(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    season = callback.data.split(":")[1]
    await state.update_data(season=season)

    await callback.message.edit_text(
        "🏷 <b>Введите название бренда</b>\n\n"
        "🛑 Напишите <code>отмена</code>, чтобы выйти на любом этапе.",
        parse_mode='HTML'
    )
    await state.set_state(SubmitItemStates.waiting_brand)


@user_router.message(SubmitItemStates.waiting_brand)
async def process_brand(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text:
        await message.answer("⚠️ Пожалуйста, введите название бренда или 'отмена' для выхода.")
        return

    await state.update_data(brand=message.text.strip())

    await message.answer(
        "<b>🛠 Введите параметры товара</b>\n\n"
        "<b>🔹 Для шин:</b> в формате <code>ширина/профиль</code>\n"
        "Пример: <code>185/65</code>\n\n"
        "<b>🔹 Для дисков:</b> в формате <code>ширина/PCD/ET/ЦО</code>\n"
        "Пример: <code>6.5/5x114.3/ET38/ЦО67.1</code>\n\n"
        "Введите <code>отмена</code>, чтобы прервать операцию.",
        parse_mode='HTML'
    )
    await state.set_state(SubmitItemStates.waiting_params)


@user_router.message(SubmitItemStates.waiting_params)
async def process_params(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text:
        await message.answer("⚠️ Пожалуйста, введите параметры шины или 'отмена' для выхода.")
        return

    await state.update_data(params=text)

    await message.answer(
        "🛠 Опишите состояние / износ / дефекты\n"
        "Введите 'отмена' для прерывания",
        parse_mode='HTML'
    )
    await state.set_state(SubmitItemStates.waiting_description)


@user_router.message(SubmitItemStates.waiting_description)
async def process_description(message: Message, state: FSMContext):
    text = message.text.strip().lower()
    if not text:
        await message.answer("⚠️ Опишите недочёты или напишите 'Нет', либо 'отмена' для выхода.")
        return

    await state.update_data(description=message.text.strip())

    await message.answer(
        "<b>🔢 Введите количество</b>\n\n"
        "Укажите, сколько единиц товара вы хотите предложить\n"
        "Например: <code>4</code>\n\n"
        "Введите <code>отмена</code>, чтобы прервать операцию",
        parse_mode="HTML"
    )
    await state.set_state(SubmitItemStates.waiting_amount)


@user_router.message(SubmitItemStates.waiting_amount)
async def process_amount(message: Message, state: FSMContext):
    text = message.text.strip().lower()
    if not text.isdigit():
        await message.answer("⚠️ Введите корректное количество или 'отмена' для выхода.")
        return

    await state.update_data(amount=int(text))

    await message.answer(
        "💰 Введите цену в рублях (только цифры)\n"
        "Пример: <code>15000</code>",
        parse_mode='HTML'
    )
    await state.set_state(SubmitItemStates.waiting_price)


@user_router.message(SubmitItemStates.waiting_price)
async def process_price(message: Message, state: FSMContext):
    text = message.text.strip().lower()
    if not text.isdigit():
        await message.answer("⚠️ Введите корректное число стоимости или 'отмена' для выхода.")
        return

    await state.update_data(price=int(text))

    await message.answer(
        "📸 Теперь отправьте фотографии\nДождитесь полной загрузки изображений и нажмите '✅ Готово' на клавиатуре",
        parse_mode='HTML',
        reply_markup=catalog_kb.success_upload_picture
    )
    await state.update_data(photos=[])
    await state.set_state(SubmitItemStates.waiting_picture)


@user_router.message(SubmitItemStates.waiting_picture)
async def handle_media_group(message: Message, state: FSMContext):
    data = await state.get_data()
    current_photos = data.get("photos", [])

    if message.text == "✅ Готово":
        if current_photos:
            await message.answer("Формирую предпросмотр...", reply_markup=ReplyKeyboardRemove())
            await preview_submission(message, state)
            return

    if not message.photo:
        await message.answer("⚠️ Пожалуйста, отправьте фото или нажмите ✅ Готово, если закончили.")
        return

    if len(current_photos) >= 10:
        await message.answer("⚠️ Максимум 10 фото. Нажмите ✅ Готово для продолжения.")
        return

    new_photo_id = message.photo[-1].file_id

    current_photos.append(new_photo_id)
    await state.update_data(photos=current_photos)

async def preview_submission(message: Message, state: FSMContext):
    data = await state.get_data()

    category = await ItemService.get_category_by_id(int(data["category_id"]))
    type_label = "Б/У Шины" if data["type_id"] == 1 else "Б/У Диски"

    caption = (
        f"<b>📦 ПРЕДПРОСМОТР ПОЗИЦИИ</b>\n\n"
        f"🔹 <b>Тип:</b> {type_label}\n"
        f"🔹 <b>Диаметр:</b> {category.value}\n"
    )

    if data["type_id"] == 1 and "season" in data:
        emoji = "☀️" if data["season"] == "summer" else "❄️"
        caption += f"<b>🔹 Сезон:</b> {emoji} { 'Лето' if data['season'] == 'summer' else 'Зима' }\n"

    caption += (
        f"🔹 <b>Бренд:</b> {data['brand']}\n"
        f"🔹 <b>Параметры:</b> {data['params']}\n"
        f"🔹 <b>Описание:</b>\n{data['description']}\n\n"
        f"📦 <b>Количество:</b> {data['amount']} шт.\n"
        f"💰 <b>Цена:</b> {data['price']} ₽"
    )

    media = MediaGroupBuilder()
    photos = data.get("photos", [])
    for i, photo_id in enumerate(photos):
        if i == 0:
            media.add_photo(media=photo_id, caption=caption, parse_mode='HTML')
        else:
            media.add_photo(media=photo_id)
    keyboard = await catalog_kb.confirm_submission_keyboard()
    await message.answer_media_group(media.build())
    await message.answer(
        "Проверьте введённые данные. Всё верно?",
        reply_markup=keyboard
    )


@user_router.callback_query(F.data.startswith('submit_confirm:'))
async def confirm_submission(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    params = callback.data.split(":")[1]
    if params == 'no':
        await state.clear()
        await callback.message.answer(f"❌ Операция отмена")
        await main_menu(callback, state)
        return

    data = await state.get_data()

    category = await ItemService.get_category_by_id(int(data["category_id"]))
    type_label = "Б/У Шины" if data["type_id"] == 1 else "Б/У Диски"

    user = await rq.get_user_by_tg_id(callback.from_user.id)

    caption = (
        f"<b>📦 Новая заявка от клиента</b>\n\n"
        f"🔹 <b>Тип:</b> {type_label}\n"
        f"🔹 <b>Диаметр:</b> {category.value}\n"
        f"🔹 <b>Бренд:</b> {data['brand']}\n"
        f"🔹 <b>Параметры:</b> {data['params']}\n"
        f"🔹 <b>Описание:</b>\n{data['description']}\n"
        f"🔹 <b>Количество:</b> {data['amount']} шт.\n"
        f"💰 <b>Цена:</b> {data['price']} ₽\n\n"
        f"📱 <b>Номер клиента:</b> {user.mobile_phone}"
    )

    media = MediaGroupBuilder()
    for i, photo_id in enumerate(data.get("photos", [])):
        if i == 0:
            media.add_photo(media=photo_id, caption=caption, parse_mode='HTML')
        else:
            media.add_photo(media=photo_id)

    await callback.bot.send_media_group(chat_id=TIRES_AND_DISCS_CHANNEL, media=media.build())

    keyboard = await catalog_kb.admin_review_submission_keyboard(callback.from_user.id)

    await callback.bot.send_message(
        chat_id=TIRES_AND_DISCS_CHANNEL,
        text="🔎 Обработать заявку:",
        reply_markup=keyboard
    )

    await callback.message.edit_text("✅ Спасибо! Ваша заявка отправлена, мы скоро с вами свяжемся")
    await state.clear()


@admin_router.callback_query(F.data.startswith("submit_admin_action:"))
async def handle_submit_admin_action(callback: CallbackQuery):
    await callback.answer()

    _, action, user_id_str = callback.data.split(":")
    telegram_user_id = int(user_id_str)

    user = f"@{callback.from_user.username}" if callback.from_user.username else callback.from_user.id

    if action == "yes":
        text = f"✅ Пользователь: {user} пригласил клиента"
        user_message = (
            "🎉 Ваша заявка одобрена!\n\n"
            "📍 Ждем вас в рабочее время по адресу:\n"
            "г. Тюмень, ул. Правды 64А (Шиномарт)"
        )
    elif action == "no":
        text = f"❌ Пользователь: {user} отклонил клиенту"
        user_message = (
            "😔 К сожалению, ваша заявка была отклонена.\n"
            "Вы можете попробовать снова позже"
        )
    else:
        await callback.message.edit_reply_markup()
        return

    await callback.message.edit_text(text=text)

    try:
        await callback.bot.send_message(
            chat_id=telegram_user_id,
            text=user_message
        )
    except Exception as e:
        await callback.message.answer(f"⚠️ Не удалось отправить сообщение клиенту: {e}")

