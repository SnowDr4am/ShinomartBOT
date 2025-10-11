from functools import wraps

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InputMediaPhoto

from ..main import employee_router, media_router
from app.utils.states import EmployeeStates
import app.keyboards.employee.close_work_day as kb
from app.servers.config import OWNER
import app.database.requests as rq


def cancel_action(func):
    @wraps(func)
    async def wrapper(message: Message, state: FSMContext, *args, **kwargs):
        if message.text == "❌ Отмена":
            await state.clear()
            return await message.answer("❌ Действие отменено")
        return await func (message, state, *args, **kwargs)
    return wrapper


def float_only(func):
    @wraps(func)
    async def wrapper(message: Message, state: FSMContext, *args, **kwargs):
        try:
            float(message.text.replace(",", "."))
        except (ValueError, TypeError):
            return await message.answer("⚠️ Пожалуйста, введите число (например, 12.5)")
        return await func(message, state, *args, **kwargs)
    return wrapper


@employee_router.message(F.text=='✅ Завершить смену')
async def start_close_work_day(message: Message, state: FSMContext):
    await message.answer(
        f"💠 <b>Введите сумму в Карте CRM</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"Введите общую сумму, которая указана в карте CRM",
        parse_mode='HTML'
    )
    await state.set_state(EmployeeStates.close_waiting_amount_crm)


@employee_router.message(EmployeeStates.close_waiting_amount_crm)
@cancel_action
@float_only
async def handle_amount_crm(message: Message, state: FSMContext):
    value_crm = float(message.text.replace(",", "."))
    await state.update_data(value_crm=value_crm)

    await message.answer(
        f"💳 <b>Введите сумму транзакций по карте</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"Укажите сумму по эквайрингу / терминалу",
        parse_mode='HTML'
    )
    await state.set_state(EmployeeStates.close_waiting_amount_cashless)


@employee_router.message(EmployeeStates.close_waiting_amount_cashless)
@cancel_action
@float_only
async def handle_amount_cashless(message: Message, state: FSMContext):
    value_cashless = float(message.text.replace(",", "."))
    await state.update_data(value_cashless=value_cashless)

    await message.answer(
        f"💠 <b>Введите сумму транзакций по СБП</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"Введите общую сумму переводов по системе быстрых платежей (СБП)",
        parse_mode='HTML'
    )
    await state.set_state(EmployeeStates.close_waiting_amount_sbp)


@employee_router.message(EmployeeStates.close_waiting_amount_sbp)
@cancel_action
@float_only
async def handle_amount_spb(message: Message, state: FSMContext):
    value_sbp = float(message.text.replace(",", "."))
    await state.update_data(value_sbp=value_sbp)

    data = await state.get_data()
    value_crm, value_cashless = float(data.get("value_crm")), float(data.get("value_cashless"))

    diff = value_crm - (value_sbp + value_cashless)
    if abs(diff) > 0.01:
        await state.set_state(EmployeeStates.close_waiting_comment)
        return await message.answer(
            f"⚠️ <b>Несоответствие суммы!</b>\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"Сумма в <b>CRM</b> не совпадает с указанными суммами по <b>эквайрингу</b> и <b>СБП</b>\n\n"
            f"📝 <b>Напишите причину расхождения:</b>",
            parse_mode='HTML'
        )

    await message.answer(
        f"💵 <b>Введите сумму транзакций переводов</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"Укажите общую сумму переводов",
        parse_mode='HTML'
    )
    await state.set_state(EmployeeStates.close_waiting_amount_transfer)


@employee_router.message(EmployeeStates.close_waiting_comment)
@cancel_action
async def handle_comment(message: Message, state: FSMContext):
    comment = message.text
    await state.update_data(comment=comment)

    await message.answer(
        f"💵 <b>Введите сумму транзакций переводов</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"Укажите общую сумму переводов",
        parse_mode='HTML'
    )
    await state.set_state(EmployeeStates.close_waiting_amount_transfer)


@employee_router.message(EmployeeStates.close_waiting_amount_transfer)
@cancel_action
@float_only
async def handle_amount_transfers(message: Message, state: FSMContext):
    value_transfers = float(message.text.replace(",", "."))
    await state.update_data(value_transfers=value_transfers)

    await message.answer(
        f"💵 <b>Введите сумму транзакций по наличке</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"Укажите общую сумму по наличным расчётам",
        parse_mode='HTML'
    )
    await state.set_state(EmployeeStates.close_waiting_amount_cash)


@employee_router.message(EmployeeStates.close_waiting_amount_cash)
@cancel_action
@float_only
async def handle_amount_cash(message: Message, state: FSMContext):
    value_cash = float(message.text.replace(",", "."))
    await state.update_data(value_cash=value_cash, photos=[])

    await message.answer(
        f"📸 <b>Прикрепите фотоотчёт</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"Загрузите фотографии чеков или документов\n"
        f"После загрузки всех необходимых фото — нажмите кнопку <b>«Готово»</b>",
        parse_mode='HTML'
    )
    await state.set_state(EmployeeStates.close_waiting_picture)


@media_router.message(EmployeeStates.close_waiting_picture)
async def handle_picture(message: Message, state: FSMContext, album: list[Message] = None):
    data = await state.get_data()
    current_photos = data.get("photos", [])

    if album:
        for msg in album:
            if msg.photo:
                file_id = msg.photo[-1].file_id
                current_photos.append(file_id)

        await state.update_data(photos=current_photos)
        return await message.answer(
            f"📷 <b>Загружено фото:</b> {len(current_photos)}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"Можете добавить ещё или нажмите <b>«Готово»</b> для продолжения",
            parse_mode='HTML',
            reply_markup=kb.complete_photo_report
        )
    if message.photo:
        file_id = message.photo[-1].file_id
        current_photos.append(file_id)
        await state.update_data(photos=current_photos)
        return await message.answer(
            f"📷 <b>Загружено фото:</b> {len(current_photos)}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"Можете добавить ещё или нажмите <b>«Готово»</b> для продолжения",
            parse_mode='HTML',
            reply_markup=kb.complete_photo_report
        )

    await message.answer("⚠️ Пожалуйста, отправьте фото или нажмите ✅ Готово")


@employee_router.callback_query(F.data.startswith("close_work_day:"))
async def handle_complete_close_work_day(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    data = await state.get_data()

    value_crm = float(data.get("value_crm"))
    value_sbp = float(data.get("value_sbp"))
    value_cashless = float(data.get("value_cashless"))
    value_cash = float(data.get("value_cash"))
    value_transfers = float(data.get("value_transfers"))
    photos = data.get("photos", [])[:10]
    comment = data.get("comment", "")

    worker = await rq.get_user_by_tg_id(callback.from_user.id)
    tg_worker = callback.from_user

    tg_link = ""
    if tg_worker and tg_worker.username:
        tg_link = f"<a href='https://t.me/{tg_worker.username}'>@{tg_worker.username}</a>"
    elif tg_worker:
        tg_link = f"<a href='tg://user?id={tg_worker.id}'>Профиль</a>"

    fmt = lambda x: f"{x:,.2f}".replace(",", " ").replace(".", ",")

    message_text = (
        f"💼 <b>Завершение смены</b>\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        
        f"📂 <b>Кто завершил</b>\n"
        f"• Имя: {worker.name}\n"
        f"• Telegram: {tg_link}\n\n"

        f"💰 <b>Финансовый отчёт:</b>\n"
        f"• Сумма по CRM: {fmt(value_crm)}\n"
        f"• Сумма по безналу: {fmt(value_cashless)}\n"
        f"• Сумма по СБП: {fmt(value_sbp)}\n\n"
        f"• Сумма по переводам: {fmt(value_transfers)}\n"
        f"• Сумма по наличке: {fmt(value_cash)}\n\n"
    )

    if comment:
        difference = value_crm - (value_sbp+value_cashless)

        message_text += (
            f"⚠️ <b>Замечено расхождение в суммах</b>\n"
            f"• Разница: {fmt(difference)}\n"
            f"• Комментарий: {comment}"
        )

    bot = callback.message.bot
    if photos:
        media = [InputMediaPhoto(media=photos[0], caption=message_text, parse_mode='HTML')]
        media += [InputMediaPhoto(media=file_id) for file_id in photos[1:]]

        try:
            await bot.send_media_group(chat_id=OWNER, media=media)
        except Exception:
            await bot.send_message(chat_id=OWNER, text=message_text, parse_mode="HTML")
            await bot.send_media_group(
                chat_id=OWNER,
                media=[InputMediaPhoto(media=file_id) for file_id in photos],
            )
    else:
        await bot.send_message(chat_id=OWNER, text=message_text, parse_mode="HTML")

    await callback.message.answer(
        f"✅ <b>Отчёт успешно сформирован!</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🎉 Ваша смена <b>успешно закрыта</b>\n"
        f"Хорошего отдыха! 💪",
        parse_mode='HTML'
    )

    await state.clear()