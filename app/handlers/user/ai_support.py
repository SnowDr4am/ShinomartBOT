from aiogram import F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from datetime import datetime
import json
import re
import pytz
import os

from app.handlers.main import ai_router
from app.servers.ai.generate import ai_generate
from app.handlers.user.user import cmd_start
from app.handlers.sched_handlers import update_channel_message
import app.database.requests as common_rq
import app.database.ai_requests as ai_rq
import app.keyboards.user.user as kb


class Gen(StatesGroup):
    inactive = State()
    waiting_for_input = State()
    waiting_for_car_type = State()
    waiting_for_radius = State()
    waiting_for_time = State()
    waiting_for_confirmation = State()
    waiting_for_repair_choice = State()


EKATERINBURG_TZ = pytz.timezone('Asia/Yekaterinburg')

PRICE_LIST = {
    "Сезонная замена шин": {
        "Легковая": {"R14": 2400, "R15": 2600, "R16": 3000, "R17": 3200, "R18": 3400, "R19": 4000, "R20": 4200,
                     "R21": 4500, "R22": 5000},
        "Внедорожник": {"R16": 3400, "R17": 3800, "R18": 4200, "R19": 4600, "R20": 5000, "R21": 5500, "R22": 6000}
    },
    "Ремонт прокола": {
        "Установка жгута": {
            "Легковая": {"R14": 600, "R15": 600, "R16": 600, "R17": 600, "R18": 600, "R19": 600,
                         "R20": 600, "R21": 600, "R22": 600},
            "Внедорожник": {"R16": 700, "R17": 700, "R18": 700, "R19": 700, "R20": 700, "R21": 700,
                            "R22": 700}
        },
        "Установка кордового пластыря": {
            "Легковая": {"R14": 1400, "R15": 1500, "R16": 1600, "R17": 1700, "R18": 1800, "R19": 1900, "R20": 2000,
                         "R21": 2100, "R22": 2200},
            "Внедорожник": {"R16": 1700, "R17": 1800, "R18": 1950, "R19": 2100, "R20": 2200, "R21": 2400, "R22": 2500}
        },
        "Вулканизация (боковой порез)": {
            "Легковая": {"R14": 2500, "R15": 2500, "R16": 2500, "R17": 2500, "R18": 2500, "R19": 2500,
                         "R20": 2500, "R21": 2500, "R22": 2500},
            "Внедорожник": {"R16": 2500, "R17": 2500, "R18": 2500, "R19": 2500, "R20": 2500, "R21": 2500,
                            "R22": 2500}
        }
    },
    "Правка диска": {
        "Легковая": {"R14": 1500, "R15": 1600, "R16": 2000, "R17": 2200, "R18": 2500, "R19": 3000, "R20": 3500,
                     "R21": 4000, "R22": 4000},
        "Внедорожник": {"R16": 2200, "R17": 2400, "R18": 3000, "R19": 3500, "R20": 4000, "R21": 4500, "R22": 5000}
    },
    "Дошиповка": {
        "Легковая": {"R14": 20, "R15": 20, "R16": 20, "R17": 20, "R18": 20, "R19": 20, "R20": 20, "R21": 20, "R22": 20},
        "Внедорожник": {"R16": 20, "R17": 20, "R18": 20, "R19": 20, "R20": 20, "R21": 20, "R22": 20}
    }
}

COMPLEX_DESCRIPTION = {
    "Сезонная замена шин": """В стоимость входит:
1) снятие установка колес
2) демонтаж монтаж
3) балансировка
4) проверка колеса на геометрию
5) мойка колес
6) пакеты""",
    "Ремонт прокола": "",
    "Правка диска": "Цена указана без учета шиномонтажа.",
    "Дошиповка": """Ремонтные шипы отличаются от заводских увеличенным диаметром основания. Это позволяет надежно закрепить их в старых, изношенных отверстиях. Таким образом, использование ремшипов - экономичный способ продлить срок службы зимней резины.""",
    "Вулканизация (боковой порез)": """Вулканизацией называют технологию, которая используется для производства резины. Для этого применяют натуральный или искусственный каучук, который в процессе обработки преобразуется в резину. Благодаря этой процедуре каучук получает новые свойства: становится более прочным и эластичным, устойчивым к воздействию агрессивной химии, слишком высокой или низкой температуры."""
}


@ai_router.callback_query(F.data == "entry_server")
async def process_entry_server(callback: CallbackQuery, state: FSMContext):
    user_id = str(callback.from_user.id)
    appointment = await ai_rq.get_active_appointment(user_id)

    if appointment:
        service_name = appointment.service.split("(")[0].strip()
        await callback.message.answer(
            f"<b>У вас уже есть запись:</b>\n{service_name} на {appointment.date_time.strftime('%H:%M %d.%m.%Y')}\n\n"
            "Вы можете отменить её, чтобы записаться заново",
            parse_mode='HTML',
            reply_markup=kb.cancel_appointment_keyboard
        )
    else:
        await callback.message.answer(
            "🛠️ <b>Мы предоставляем следующие услуги:</b>\n\n"
            "1️⃣ Сезонная замена шин\n"
            "2️⃣ Ремонт прокола\n"
            "3️⃣ Правка диска\n"
            "4️⃣ Дошиповка\n\n"
            "🤝 <b>Чем могу помочь?</b> 🤔\n\n"
            "ℹ️ Чтобы отменить запись, напишите <code>отмена</code>",
            parse_mode='HTML'
        )
        await state.set_state(Gen.waiting_for_input)
    await callback.answer()


@ai_router.callback_query(F.data == "appointment_delete")
async def process_cancel_appointment(callback: CallbackQuery, state: FSMContext):
    user_id = str(callback.from_user.id)

    appointment = await ai_rq.get_active_appointment(user_id)
    if not appointment:
        await callback.message.edit_text(
            "❌ <b>Ошибка:</b>\nЗапись не найдена. Возможно, она уже удалена.\nПопробуйте позже",
            parse_mode='HTML'
        )
        await callback.answer()
        return

    current_time = datetime.now(EKATERINBURG_TZ)
    current_date = current_time.date()
    appointment_date = appointment.date_time.date()
    is_today = current_date == appointment_date

    success = await ai_rq.cancel_appointment(user_id)
    if success:
        await state.clear()
        await callback.answer("Запись отменена\nТеперь вы можете записаться заново через меню", show_alert=True)
        await callback.message.delete()
        await state.set_state(Gen.inactive)

        if is_today:
            await update_channel_message(callback.bot)
    else:
        await callback.message.edit_text(
            "❌ <b>Ошибка:</b>\nНе удалось отменить запись. Попробуйте позже",
            parse_mode='HTML'
        )
    await callback.answer()


@ai_router.message(F.text.lower().in_({"отмена", "отменить", "отменить операцию", "отмени", "стоп", "прекратить"}))
async def cancel_operation(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Gen.inactive)
    await cmd_start(message)


@ai_router.message(Gen.waiting_for_car_type)
async def process_car_type(message: Message, state: FSMContext):
    params_response = await ai_generate(message.text, mode="params")
    if not params_response:
        await message.answer(
            "❌ <b>Ошибка:</b>\nНет связи с ИИ. Свяжитесь с нами по телефону 📞\n\nℹ️ Для отмены напишите <code>отмена</code>",
            parse_mode='HTML')
        return

    json_match = re.search(r'\{.*\}', params_response, re.DOTALL)
    if not json_match:
        await message.answer(
            "<b>Уточните тип машины:</b>\nЛегковая или Внедорожник?\n\nℹ️ Для отмены напишите <code>отмена</code>",
            parse_mode='HTML')
        return
    params = json.loads(json_match.group(0))

    if "error" in params:
        await message.answer(f"❌ <b>Ошибка:</b>\n{params['error']}\n\nℹ️ Для отмены напишите <code>отмена</code>",
                             parse_mode='HTML')
        return

    data = await state.get_data()
    service = data.get("service", "Сезонная замена шин").rstrip(".")
    car_type = params.get("car_type")
    radius = params.get("radius") or data.get("radius")

    if car_type not in ["Легковая", "Внедорожник"]:
        await message.answer(
            "<b>Уточните тип машины:</b>\nЛегковая или Внедорожник?\n\nℹ️ Для отмены напишите <code>отмена</code>",
            parse_mode='HTML')
        return

    await state.update_data(car_type=car_type)
    base_service = service.split(" — ")[0] if "Ремонт прокола" in service else service
    if base_service not in PRICE_LIST:
        await message.answer(
            "❌ <b>Ошибка:</b>\nУслуга не найдена. Начните заново\n\nℹ️ Для отмены напишите <code>отмена</code>",
            parse_mode='HTML')
        await state.clear()
        return

    if radius:
        radius = radius.upper()
        valid_radii = (PRICE_LIST[base_service][car_type].keys() if base_service != "Ремонт прокола" else
                       PRICE_LIST["Ремонт прокола"]["Установка кордового пластыря"][car_type].keys())
        if radius in valid_radii:
            await state.update_data(radius=radius)
            await finalize_service(message, state)
        else:
            radius_range = "R14–R22" if car_type == "Легковая" else "R16–R22"
            await message.answer(
                f"❌ <b>Ошибка:</b>\nРадиус не в диапазоне {radius_range}\n\nℹ️ Для отмены напишите <code>отмена</code>",
                parse_mode='HTML')
            await state.set_state(Gen.waiting_for_radius)
    else:
        radius_range = "R14–R22" if car_type == "Легковая" else "R16–R22"
        await message.answer(
            f"⚙️ <b>{service} ({car_type})</b>\n\nКакой радиус дисков? ({radius_range})\n\nℹ️ Для отмены напишите <code>отмена</code>",
            parse_mode='HTML')
        await state.set_state(Gen.waiting_for_radius)


@ai_router.message(Gen.waiting_for_radius)
async def process_radius(message: Message, state: FSMContext):
    params_response = await ai_generate(message.text, mode="params")
    if not params_response:
        await message.answer(
            "❌ <b>Ошибка:</b>\nНет связи с ИИ. Свяжитесь с нами по телефону 📞\n\nℹ️ Для отмены напишите <code>отмена</code>",
            parse_mode='HTML')
        return

    json_match = re.search(r'\{.*\}', params_response, re.DOTALL)
    if not json_match:
        await message.answer("⚙️ <b>Радиус дисков:</b>\nНапример, R16\n\nℹ️ Для отмены напишите <code>отмена</code>",
                             parse_mode='HTML')
        return
    params = json.loads(json_match.group(0))

    if "error" in params:
        await message.answer(f"❌ <b>Ошибка:</b>\n{params['error']}\n\nℹ️ Для отмены напишите <code>отмена</code>",
                             parse_mode='HTML')
        return

    data = await state.get_data()
    service = data.get("service", "Сезонная замена шин").rstrip(".")
    car_type = data.get("car_type") or params.get("car_type")
    radius = params.get("radius")

    if not radius:
        radius_range = "R14–R22" if car_type == "Легковая" else "R16–R22"
        await message.answer(
            f"⚙️ <b>Радиус дисков:</b>\nНапример, R16 ({radius_range})\n\nℹ️ Для отмены напишите <code>отмена</code>",
            parse_mode='HTML')
        return

    if car_type not in ["Легковая", "Внедорожник"]:
        await state.update_data(radius=radius.upper())
        await message.answer(
            "<b>Уточните тип машины:</b>\nЛегковая или Внедорожник?\n\nℹ️ Для отмены напишите <code>отмена</code>",
            parse_mode='HTML')
        await state.set_state(Gen.waiting_for_car_type)
        return

    base_service = service.split(" — ")[0] if "Ремонт прокола" in service else service
    if base_service not in PRICE_LIST:
        await message.answer(
            "❌ <b>Ошибка:</b>\nУслуга не найдена. Начните заново\n\nℹ️ Для отмены напишите <code>отмена</code>",
            parse_mode='HTML')
        await state.clear()
        return

    radius = radius.upper()
    valid_radii = (PRICE_LIST[base_service][car_type].keys() if base_service != "Ремонт прокола" else
                   PRICE_LIST["Ремонт прокола"]["Установка кордового пластыря"][car_type].keys())
    if radius in valid_radii:
        await state.update_data(car_type=car_type, radius=radius)
        await finalize_service(message, state)
    else:
        radius_range = "R14–R22" if car_type == "Легковая" else "R16–R22"
        await message.answer(
            f"❌ <b>Ошибка:</b>\nРадиус не в диапазоне {radius_range}\n\nℹ️ Для отмены напишите <code>отмена</code>",
            parse_mode='HTML')


@ai_router.message(Gen.waiting_for_repair_choice)
async def process_repair_choice(message: Message, state: FSMContext):
    choice = message.text.strip()
    if choice not in ["1", "2", "3"]:
        await message.answer(
            "<b>Услуга: Ремонт прокола</b>\n\n"
            "<b>Мы предлагаем три варианта:</b>\n"
            "1) Установка жгута — временный ремонт, без гарантии\n"
            "<b>2) Установка кордового пластыря — профессиональный ремонт, гарантия 1 год\n"
            "3) Вулканизация — профессиональный ремонт боковых порезов\n"
            "Какой вариант вам подходит? Выберите 1, 2 или 3. ℹ️</b>\n\n"
            "ℹ️ Для отмены напишите <code>отмена</code>",
            parse_mode='HTML'
        )
        return

    repair_type = {
        "1": "Установка жгута",
        "2": "Установка кордового пластыря",
        "3": "Вулканизация (боковой порез)"
    }[choice]
    await state.update_data(service=f"Ремонт прокола — {repair_type}")
    await message.answer(
        "<b>Уточните тип машины:</b>\nЛегковая или Внедорожник?\n\nℹ️ Для отмены напишите <code>отмена</code>",
        parse_mode='HTML')
    await state.set_state(Gen.waiting_for_car_type)


async def finalize_service(message: Message, state: FSMContext):
    data = await state.get_data()
    service = data.get("service", "Сезонная замена шин").rstrip(".")
    car_type = data.get("car_type")
    radius = data.get("radius")

    if not all([car_type, radius]):
        await message.answer(
            "❌ <b>Ошибка:</b>\nНет данных о машине или радиусе. Начните заново\n\nℹ️ Для отмены напишите <code>отмена</code>",
            parse_mode='HTML')
        await state.clear()
        return

    base_service = service.split(" — ")[0] if "Ремонт прокола" in service else service
    repair_type = service.split(" — ")[1] if "Ремонт прокола" in service else None
    if base_service not in PRICE_LIST:
        await message.answer(
            "❌ <b>Ошибка:</b>\nУслуга не найдена. Начните заново\n\nℹ️ Для отмены напишите <code>отмена</code>",
            parse_mode='HTML')
        await state.clear()
        return

    price = (PRICE_LIST[base_service][car_type][radius] if base_service != "Ремонт прокола" else
             PRICE_LIST["Ремонт прокола"][repair_type][car_type][radius])

    full_service = f"{base_service}{' — ' + repair_type if repair_type else ''} ({car_type}, {radius})"
    await state.update_data(service=full_service)
    price_text = f"{'от ' if repair_type == 'Вулканизация (боковой порез)' else ''}{price} ₽{'/шип' if 'Дошиповка' in base_service else ''}"
    extra_info = COMPLEX_DESCRIPTION.get(base_service if not repair_type else repair_type, "")
    if repair_type == "Установка жгута":
        extra_info = "Временный ремонт, без гарантии"
    elif repair_type == "Установка кордового пластыря":
        extra_info = "Профессиональный ремонт, гарантия 1 год"

    response = f"🛠️ <b>{full_service}</b> — {price_text}\n\n{extra_info}\n\n⏰ <b>На какое время записать?</b>\n\nℹ️ Для отмены напишите <code>отмена</code>"

    if repair_type == "Вулканизация (боковой порез)":
        photo_path = os.path.join("app", "temp", "vulkan.jpg")
        photo = FSInputFile(photo_path)
        await message.answer_photo(
            photo=photo,
            caption=response,
            parse_mode='HTML'
        )
    elif base_service == "Дошиповка":
        photo_path = os.path.join("app", "temp", "ship.jpg")
        photo = FSInputFile(photo_path)
        await message.answer_photo(
            photo=photo,
            caption=response,
            parse_mode='HTML'
        )
    else:
        await message.answer(response, parse_mode='HTML')
    await state.set_state(Gen.waiting_for_time)


@ai_router.message(Gen.waiting_for_confirmation)
async def process_confirmation(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    data = await state.get_data()
    service = data.get("service")
    next_time = data.get("next_time")

    if not all([service, next_time]):
        await message.answer(
            "❌ <b>Ошибка:</b>\nДанные потеряны. Начните заново\n\nℹ️ Для отмены напишите <code>отмена</code>",
            parse_mode='HTML')
        await state.clear()
        return

    if message.text.lower().strip() in ["да", "yes", "ок", "подходит"]:
        next_time = EKATERINBURG_TZ.localize(next_time) if next_time.tzinfo is None else next_time
        user_data = await common_rq.get_user_profile(user_id)
        appointment = await ai_rq.add_appointment(user_id, next_time, service, user_data['mobile_phone'])
        if not appointment:
            await message.answer(
                "❌ <b>Ошибка:</b>\nУ вас уже есть запись\n\nℹ️ Для отмены напишите <code>отмена</code>",
                parse_mode='HTML')
            return

        current_time = datetime.now(EKATERINBURG_TZ)
        current_date = current_time.date()
        appointment_date = next_time.date()
        is_today = current_date == appointment_date

        await message.answer(f"✅ <b>Запись:</b>\n{service} на {next_time.strftime('%H:%M %d.%m.%Y')}\n\nЖдем вас!",
                             parse_mode='HTML')
        await state.clear()
        await state.set_state(Gen.inactive)
        await cmd_start(message)

        if is_today:
            await update_channel_message(message.bot)
    else:
        await message.answer(
            "⏰ <b>Укажите новое время:</b>\nНапример, 'сегодня в 14:00'\n\nℹ️ Для отмены напишите <code>отмена</code>",
            parse_mode='HTML')
        await state.set_state(Gen.waiting_for_time)


@ai_router.message(Gen.waiting_for_time)
async def process_time(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    data = await state.get_data()
    service = data.get("service")

    if not service:
        await message.answer(
            "❌ <b>Ошибка:</b>\nУслуга не выбрана. Начните заново\n\nℹ️ Для отмены напишите <code>отмена</code>",
            parse_mode='HTML')
        await state.clear()
        return

    time_response = await ai_generate(message.text, mode="time")
    if not time_response:
        await message.answer(
            "❌ <b>Ошибка:</b>\nНет связи с ИИ. Свяжитесь с нами по телефону 📞\n\nℹ️ Для отмены напишите <code>отмена</code>",
            parse_mode='HTML')
        return

    try:
        time_data = json.loads(time_response)
        date_time = EKATERINBURG_TZ.localize(
            datetime.strptime(f"{time_data['date']} {time_data['time']}", "%d.%m.%Y %H:%M"))
    except (json.JSONDecodeError, ValueError, KeyError):
        await message.answer(
            "❌ <b>Ошибка:</b>\nУкажите время, например, 'сегодня в 14:00'\n\nℹ️ Для отмены напишите <code>отмена</code>",
            parse_mode='HTML')
        return

    current_time = datetime.now(EKATERINBURG_TZ)
    if date_time < current_time:
        await message.answer(
            "❌ <b>Ошибка:</b>\nВремя в прошлом. Укажите будущее\n\nℹ️ Для отмены напишите <code>отмена</code>",
            parse_mode='HTML')
        return

    if not (9 <= date_time.hour < 21):
        await message.answer(
            "⏳ <b>Работаем с 9:00 до 21:00</b>\n\nУкажите время в этом диапазоне\n\nℹ️ Для отмены напишите <code>отмена</code>",
            parse_mode='HTML')
        return

    if await ai_rq.check_availability(date_time):
        user_data = await common_rq.get_user_profile(user_id)
        if not user_data.get('mobile_phone'):
            await message.answer(
                "❌ <b>Ошибка:</b>\nУкажите телефон в профиле\n\nℹ️ Для отмены напишите <code>отмена</code>",
                parse_mode='HTML')
            return
        appointment = await ai_rq.add_appointment(user_id, date_time, service, user_data['mobile_phone'])
        if not appointment:
            await message.answer(
                "❌ <b>Ошибка:</b>\nУ вас уже есть запись\n\nℹ️ Для отмены напишите <code>отмена</code>",
                parse_mode='HTML')
            return

        current_date = current_time.date()
        appointment_date = date_time.date()
        is_today = current_date == appointment_date

        await message.answer(f"✅ <b>Запись:</b>\n{service} на {date_time.strftime('%H:%M %d.%m.%Y')}\n\nЖдем вас!",
                             parse_mode='HTML')
        await state.clear()
        await state.set_state(Gen.inactive)
        await cmd_start(message)

        if is_today:
            await update_channel_message(message.bot)
    else:
        next_time = await ai_rq.find_next_available_time(date_time)
        if next_time.tzinfo is not None:
            next_time = next_time.replace(tzinfo=None)
        await state.update_data(next_time=next_time)
        await message.answer(
            f"⏳ <b>{date_time.strftime('%H:%M')} занято</b>\n\n"
            f"Свободно: {next_time.strftime('%H:%M %d.%m.%Y')}\n\n"
            "<b>Подходит?</b> (да/нет)\n\n"
            "ℹ️ Для отмены напишите <code>отмена</code>",
            parse_mode='HTML'
        )
        await state.set_state(Gen.waiting_for_confirmation)


@ai_router.message(Gen.waiting_for_input)
async def generating(message: Message, state: FSMContext):
    service_map = {"1": "Сезонная замена шин", "2": "Ремонт прокола", "3": "Правка диска", "4": "Дошиповка"}
    input_text = message.text.strip()
    service = service_map.get(input_text) or input_text

    response = await ai_generate(service, mode="service")
    if not response:
        await message.answer(
            "❌ <b>Ошибка:</b>\nНет связи с ИИ. Свяжитесь с нами по телефону 📞\n\nℹ️ Для отмены напишите <code>отмена</code>",
            parse_mode='HTML')
        return

    lines = response.split("\n")
    formatted_lines = []
    for line in lines:
        if line.startswith("Услуга:"):
            formatted_lines.append(f"<b>{line.replace('Переобувка резины', 'Сезонная замена шин')}</b>")
            formatted_lines.append("")
        elif "На какое время вас записать?" in line:
            formatted_lines.append(f"<b>{line}</b>")
        elif "Какой радиус дисков" in line:
            formatted_lines.append(f"<b>{line}</b>")
        elif "Уточните тип машины" in line:
            formatted_lines.append(f"<b>{line}</b>")
        elif "Мы предоставляем следующие услуги:" in line:
            formatted_lines.append(f"<b>{line}</b>")
            formatted_lines.append("")
        elif "Какой вариант вам подходит?" in line:
            formatted_lines.append(f"<b>{line}</b>")
            formatted_lines.append("")
        else:
            formatted_lines.append(line.replace("Переобувка резины", "Сезонная замена шин"))
    formatted_response = "\n".join(formatted_lines) + "\n\nℹ️ Для отмены напишите <code>отмена</code>"

    await message.answer(formatted_response, parse_mode='HTML')

    if "На какое время вас записать?" in response:
        service_line = response.split("Услуга: ")[1].split(" — ")[0].strip().replace("Переобувка резины",
                                                                                     "Сезонная замена шин")
        car_type = "Легковая" if "Легковая" in service_line else service_line.split(" на ")[1].split(" ")[0]
        radius = service_line.split(" ")[-1]
        await state.update_data(service=f"{service_line.split(' на ')[0]} ({car_type}, {radius})")
        await state.set_state(Gen.waiting_for_time)
    elif "Уточните тип машины" in response:
        service = response.split("Услуга: ")[1].split("\n")[0].strip().rstrip(".").replace("Переобувка резины",
                                                                                           "Сезонная замена шин")
        await state.update_data(service=service)
        await state.set_state(Gen.waiting_for_car_type)
    elif "Какой радиус дисков" in response:
        service = response.split("Услуга: ")[1].split("\n")[0].strip().rstrip(".").replace("Переобувка резины",
                                                                                           "Сезонная замена шин")
        car_type = service.split(" на ")[1].replace(" машину", "").strip()
        await state.update_data(service=service, car_type=car_type)
        await state.set_state(Gen.waiting_for_radius)
    elif "Какой вариант вам подходит?" in response:
        await state.update_data(service="Ремонт прокола")
        await state.set_state(Gen.waiting_for_repair_choice)


@ai_router.message(Gen.inactive)
async def inactive_state(message: Message):
    await message.answer("🚗 <b>Выберите услугу в меню</b>", parse_mode='HTML')