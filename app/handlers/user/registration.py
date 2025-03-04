from aiogram import F
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from datetime import datetime
import re

from app.handlers.main import user_router
import app.keyboards.user.user as kb
import app.database.requests as rq


class GetUserInfo(StatesGroup):
    name = State()
    mobile_phone = State()
    birthday = State()


@user_router.callback_query(F.data == 'registration')
async def registration(callback: CallbackQuery, state: FSMContext):
    await callback.answer("")
    await callback.message.answer(
        "Для регистрации мне необходимо собрать о Вас следующую информацию:\n"
        "— <b>Ваше имя</b>\n"
        "— <b>Ваш номер телефона</b>\n"
        "— <b>Дату рождения</b>\n\n",
        parse_mode="HTML"
    )
    await callback.message.answer(
        "Напишите, пожалуйста, Ваше имя"
    )
    await state.set_state(GetUserInfo.name)

@user_router.message(GetUserInfo.name)
async def get_name(message: Message, state: FSMContext):
    user_input = message.text

    await state.update_data(name=user_input)

    await message.answer(
        "Напишите, пожалуйста, ваш номер телефона",
        reply_markup=kb.get_phone_number
    )

    await state.set_state(GetUserInfo.mobile_phone)

@user_router.message(GetUserInfo.mobile_phone)
async def get_mobile_phone(message: Message, state: FSMContext):
    try:
        if message.contact is not None:
            phone_number = message.contact.phone_number
            cleaned_number = re.sub(r'\D', '', phone_number)
        else:
            user_input = message.text
            if not user_input:
                await message.answer("Вы не ввели номер телефона.")
                return

            cleaned_number = re.sub(r'\D', '', user_input)

        if not cleaned_number or cleaned_number[0] not in ('7', '8'):
            await message.answer("Некорректный формат номера. Номер должен начинаться с 7 или 8.")
            return

        if cleaned_number[0] == '7':
            cleaned_number = '8' + cleaned_number[1:]

        if len(cleaned_number) != 11:
            await message.answer("Некорректная длина номера. Номер должен содержать 11 цифр.")
            return

        if await rq.check_mobile_phone(cleaned_number):
            await message.answer("Номер телефона уже зарегистрирован")
            return

        await state.update_data(mobile_phone=cleaned_number)

        await state.set_state(GetUserInfo.birthday)
        await message.answer("Напишите вашу дату рождения\n"
                            "Пример: <code>26.02.2025</code>",
                             parse_mode='HTML',
                             reply_markup=ReplyKeyboardRemove())

    except Exception as e:
        print(f"Ошибка: {e}")
        await message.answer("Произошла ошибка при обработке номера телефона. Попробуйте ещё раз.")


@user_router.message(GetUserInfo.birthday)
async def get_birthday_date(message: Message, state: FSMContext):
    user_input = message.text.strip()

    try:
        cleaned_input = re.sub(r'[^0-9\.\-/]', '', user_input)

        date_formats = [
            "%Y.%m.%d", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y"
        ]

        parsed_date = None
        for date_format in date_formats:
            try:
                parsed_date = datetime.strptime(cleaned_input, date_format)
                break
            except ValueError:
                continue

        if not parsed_date:
            await message.answer("Некорректный формат даты. Используйте ДД.ММ.ГГГГ.")
            return

        formatted_date = parsed_date.strftime("%d.%m.%Y")

        await state.update_data(birthday=formatted_date)

        data = await state.get_data()
        name = data.get("name")
        number = data.get("mobile_phone")

        birthday_date_obj = parsed_date.date()

        if await rq.set_user(message.from_user.id, datetime.now(), name, number, birthday_date_obj):
            await message.answer(
                f"Регистрация завершена.\n"
                f"Имя: {name}\n"
                f"Телефон: {number}\n"
                f"Дата рождения: {formatted_date}"
            )
        else:
            await message.answer("Внутренняя ошибка. Попробуйте позже.")

    except Exception as e:
        await message.answer("Ошибка обработки даты. Попробуйте ещё раз.")
        print(f"Ошибка: {e}")