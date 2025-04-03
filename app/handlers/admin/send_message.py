import asyncio
from aiogram import F
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from app.handlers.main import admin_router, user_router
import app.keyboards.admin.admin as kb
import app.database.admin_requests as rq
from app.handlers.admin.admin import back_to_main


class Interaction(StatesGroup):
    users_list = State()
    text = State()
    photo = State()


@admin_router.callback_query(F.data == 'cancelAction')
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    await state.clear()
    await back_to_main(callback)


@admin_router.callback_query(F.data == 'instructionHTML')
async def get_instruction(callback: CallbackQuery):
    await callback.answer()

    await callback.message.answer(
        f"📝 Памятка по HTML тегам:\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔹 Жирный шрифт - <b>Текст между этими символами будет жирным</b>\n"
        f"🔹 Курсив - <i>Текст будет курсивом</i>\n"
        f"🔹 Подчеркнутый текст - <u>Текст будет подчеркнут</u>\n"
        f"🔹 Зачеркнутый текст - <s>Текст будет зачеркнут</s>\n"
        f"🔹 Текст, который можно скопировать - <code>Текст копируется</code>\n"
        f"🔹 Переход по ссылке при нажатии - <a href='ссылка'>кликабельный текст</a>\n\n"
        f"⌛️ Я все еще жду текст для рассылки в следующем сообщении",
        reply_markup=kb.delete_button_admin
    )


@user_router.callback_query(F.data == 'send_message')
async def send_message(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    users = await rq.get_tg_id_mailing()
    await callback.message.answer(
        f"✉️ <b>Напишите текст сообщения для рассылки</b>\n\n"
        f"📌 <i>Можно прикрепить фотографии, добавить к ним описание и отформатировать текст</i>\n",
        parse_mode='HTML',
        reply_markup=kb.send_message_keyboard
    )
    await state.update_data(users_list = users)
    await state.set_state(Interaction.text)

@user_router.message(Interaction.text)
async def process_message(message: Message, state: FSMContext):
    user_input = message.text or message.caption or ""
    user_input = user_input.strip()

    photo_file_id = None
    if message.photo:
        photo_file_id = message.photo[-1].file_id

    data = await state.get_data()

    await state.update_data(text=user_input, photo=photo_file_id)

    await message.answer(
        f"📢 <b>Вы собираетесь отправить сообщение {len(data['users_list'])} пользователям</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📄 <b>Содержание сообщения:</b>",
        parse_mode='HTML'
    )

    if photo_file_id:
        await message.answer_photo(
            photo=photo_file_id,
            caption=user_input,
            parse_mode='HTML',
        )
    else:
        await message.answer(
            user_input,
            parse_mode='HTML',
        )

    await message.answer(
        "🛎 <b>Подтвердите отправку рассылки:</b>",
        parse_mode='HTML',
        reply_markup=kb.confirm_button
    )

@user_router.callback_query(F.data=='confirmSendMessage')
async def confirm_send_message(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    try:
        data = await state.get_data()
        users_list = data['users_list']
        text = data['text']
        photo_file_id = data.get('photo')

        success_count = 0
        errors = []

        for user_id in users_list:
            try:
                if photo_file_id:
                    await callback.bot.send_photo(
                        chat_id=user_id,
                        photo=photo_file_id,
                        caption=text,
                        parse_mode='HTML'
                    )
                else:
                    await callback.bot.send_message(
                        chat_id=user_id,
                        text=text,
                        parse_mode='HTML'
                    )
                success_count += 1
            except TelegramForbiddenError:
                errors.append(f"Пользователь {user_id} заблокировал бота")
            except TelegramBadRequest as e:
                errors.append(f"Ошибка при отправке {user_id}: {e.message}")
            except Exception as e:
                errors.append(f"Неизвестная ошибка с {user_id}: {str(e)}")
        report_message = (
            f"📊 <b>Результаты рассылки</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ <b>Успешно отправлено:</b> {success_count}/{len(users_list)}\n"
        )

        if errors:
            report_message += (
                f"\n❌ <b>Ошибки ({len(errors)}):</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                + "\n".join(f"• {error}" for error in errors[:10])
            )
            if len(errors) > 10:
                report_message += f"\n... и ещё {len(errors) - 10} ошибок"

        await callback.message.answer(report_message, parse_mode='HTML', reply_markup=kb.delete_button_admin)
    except Exception as e:
        await callback.message.answer(f"❌ Произошла критическая ошибка: {str(e)}")
    finally:
        await state.clear()
        await back_to_main(callback)