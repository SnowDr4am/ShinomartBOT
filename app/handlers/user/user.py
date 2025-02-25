from aiogram import F
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
import datetime
import re

from app.handlers.main import user_router
import app.keyboards.user.user as kb


class GetUserInfo(StatesGroup):
    mobile_phone = State()
    birthday = State()

@user_router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "<b>Привет!</b>\n\n"
        "Я бот шиномарта, который любит мешать бухгалтеру и делать для Вас скидки\n\n",
        parse_mode="HTML",
        reply_markup=kb.registration
    )

@user_router.callback_query(F.data == 'registration')
async def registration(callback: CallbackQuery, state: FSMContext):
    await callback.answer("")
    await callback.message.answer(
        "Для начала мне необходимо собрать о Вас следующую информацию:\n"
        "— <b>Ваш номер телефона</b>\n"
        "— <b>Дату рождения</b>\n\n"
        "<i>Очень важно:</i> Если вы уже зарегистрировались в программе лояльности, "
        "Ваш номер телефона, указанный в телеграме, должен совпадать с тем, что вы назвали нашему коллеге. "
        "Если это не так — напишите от руки номер телефона.\n\n",
        parse_mode="HTML",
        reply_markup=kb.get_phone_number
    )
    await state.set_state(GetUserInfo.mobile_phone)

@user_router.message(GetUserInfo.mobile_phone)
async def get_mobile_phone(message: Message, state: FSMContext):
    user_input = message.text

    try:
        cleaned_number = re.sub(r'\D', '', user_input)

        if not cleaned_number or cleaned_number[0] not in ('7', '8'):
            await message.answer("Некорректный формат номера. Номер должен начинаться с 7 или 8.")
            return

        if cleaned_number[0] == '7':
            cleaned_number = '8' + cleaned_number[1:]

        if len(cleaned_number) != 11:
            await message.answer("Некорректная длина номера. Номер должен содержать 11 цифр.")
            return

        await state.update_data(mobile_phone=cleaned_number)

        await message.answer(f"Номер телефона успешно сохранён: {cleaned_number}")

        await state.set_state(GetUserInfo.birthday)

        await message.answer("Скажите вашу дату рождения", reply_markup=kb.get_birthday)
    except Exception as e:
        print(f"Ошибка: {e}")

@user_router.message(GetUserInfo.birthday)
async def get_birthday_date(message: Message, state: FSMContext):
    user_input = message.text

    try:
        cleaned_input = re.sub(r'[^0-9\.\-/]', '', user_input)

        date_formats = [
            "%Y.%m.%d",
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d.%m.%Y",
        ]

        parsed_date = None
        for date_format in date_formats:
            try:
                parsed_date = datetime.strptime(cleaned_input, date_format)
                break
            except ValueError:
                continue

        if not parsed_date:
            await message.answer("Некорректный формат даты. Пожалуйста, введите дату в формате ДД.ММ.ГГГГ.")
            return

        formatted_date = parsed_date.strftime("%d.%m.%Y")

        await state.update_data(birthday=formatted_date)

        await message.answer(f"Дата рождения успешно сохранена: {formatted_date}")

    except Exception as e:
        await message.answer("Произошла ошибка при обработке даты. Пожалуйста, попробуйте ещё раз.")
        print(f"Ошибка: {e}")





