from aiogram import F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from app.handlers.main import employee_router
import app.keyboards.employee.employee as kb
import app.database.requests as rq


class GetUser(StatesGroup):
    mobile_phone = State()
    select_action = State()
    amount = State()
    bonus_balance = State()
    bonus_deduction = State()
    confirm_deduction = State()



@employee_router.message(Command("job"))
async def cmd_job(message: Message):
    await message.answer("Вы перешли в меню работника\n"
                         "Все взаимодействие будет происходить через кнопки снизу",
                         parse_mode='HTML', reply_markup=kb.main_menu)


@employee_router.message(F.text == 'Новая транзакция')
async def add_bonus(message: Message, state: FSMContext):
    await message.answer("Вы выбрали 'Новая транзакция'. Введите последние 4 цифры номера телефона пользователя\n"
                         "Для выхода из этого меню нажмите 'отмена'")
    await state.set_state(GetUser.mobile_phone)


@employee_router.message(GetUser.mobile_phone)
async def send_phone_numbers(message: Message, state: FSMContext):
    user_input = message.text

    if user_input.lower() == 'отмена':
        await state.clear()
        await message.answer("Операция отменена")
        return

    if not user_input.isdigit() or len(user_input) != 4:
        await message.answer("Некорректный ввод. Введите последние 4 цифры номера телефона")
        return

    phone_numbers = await rq.get_phone_numbers_by_suffix(user_input)

    if not phone_numbers:
        await message.answer("Номер телефона не найден")
        return

    keyboard = await kb.generate_phone_numbers_keyboard(phone_numbers)
    await message.answer("Выберите номер телефона:", reply_markup=keyboard)


@employee_router.callback_query(F.data.startswith("cancel"))
async def handle_phone_selection(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    await callback.message.answer("Операция отменена")

    await state.clear()


@employee_router.callback_query(F.data.startswith("select_phone"))
async def handle_phone_selection(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    phone_number = callback.data.split(":")[1]

    user_data = await rq.get_user_by_phone(phone_number)

    if user_data:
        user_info_message = (
            "📋 <b>Профиль пользователя:</b>\n\n"
            f"👤 <b>Имя:</b> {user_data.name}\n"
            f"📞 <b>Номер телефона:</b> {user_data.mobile_phone}\n"
            f"🎂 <b>Дата рождения:</b> {user_data.birthday_date}\n"
            f"💰 <b>Бонусный баланс:</b> {user_data.bonus_balance.balance} бонусов\n"
        )

        await callback.message.answer(user_info_message, parse_mode='HTML')

        await state.update_data(phone_number=phone_number)
        await state.update_data(bonus_balance=user_data.bonus_balance.balance)

        await callback.message.answer("Выберите действие:", reply_markup=kb.new_transaction)
        await state.set_state(GetUser.select_action)
    else:
        await callback.message.answer("Профиль пользователя не найден")
        return


@employee_router.callback_query(GetUser.select_action, F.data.startswith("transaction:"))
async def handle_action_selection(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    action = callback.data.split(":")[1]

    if action == 'cancel':
        await state.clear()
        await callback.message.answer("Операция отменена")
        return

    data = await state.get_data()
    phone_number = data.get("phone_number")

    await state.update_data(select_action=action)

    if action == 'add':
        await callback.message.answer(
            f"Вы выбрали пополнение для номера {phone_number}\n"
            f"Введите, пожалуйста, сумму его покупки"
        )
        await state.set_state(GetUser.amount)
    elif action == 'remove':
        await callback.message.answer(
            f"Вы выбрали списание для номера {phone_number}\n"
            f"Введите, пожалуйста, сколько сумму его покупки"
        )
        await state.set_state(GetUser.amount)


@employee_router.message(GetUser.amount)
async def handle_amount_input(message: Message, state: FSMContext):
    user_input = message.text.strip()

    try:
        amount = float(user_input)

        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")
    except Exception as e:
        await message.answer("Некорректный ввод. Введите положительное число")
        return

    data = await state.get_data()
    phone_number = data.get("phone_number")
    action = data.get("select_action")
    bonus_balance = data.get("bonus_balance")
    await state.update_data(amount = amount)

    user_data = await rq.get_user_by_phone(phone_number)

    if not user_data:
        await message.answer('Профиль пользователя не найден')
        await state.clear()
        return

    if action == 'add':
        amount_bonus = amount*0.05
        success = await rq.set_bonus_balance(message.from_user.id, "add", amount_bonus, amount, message.from_user.id)
        if success:
            await message.answer(f"Начислено {amount_bonus:.2f} бонусов пользователю {user_data.name}")
        else:
            await message.answer(f"Возникла ошибка при зачислении бонусов")
    elif action == 'remove':
        max_bonus_deduction = amount*0.3
        if bonus_balance <= max_bonus_deduction:
            finally_bonus = bonus_balance
        else:
            finally_bonus = max_bonus_deduction
        await state.update_data(bonus_deduction=finally_bonus)
        await message.answer(f"Вы можете списать максимум {finally_bonus} бонусов с аккаунта пользователя", reply_markup=kb.confirm_transaction)
        await state.set_state(GetUser.confirm_deduction)


@employee_router.callback_query(GetUser.confirm_deduction, F.data.startswith("confirm:"))
async def confirm_deduction(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    action = callback.data.split(":")[1]
    data = await state.get_data()
    phone_number = data.get("phone_number")
    bonus_deduction = data.get("bonus_deduction")
    amount = data.get("amount")

    user_data = await rq.get_user_by_phone(phone_number)

    if not user_data:
        await callback.message.answer("Профиль пользователя не найден.")
        await state.clear()
        await callback.answer()
        return

    if action == 'no':
        amount_bonus = amount * 0.05
        success = await rq.set_bonus_balance(callback.from_user.id, "add", amount_bonus, amount, callback.from_user.id)
        if success:
            await callback.message.answer(f"Начислено {amount_bonus:.2f} бонусов пользователю {user_data.name}")
        else:
            await callback.message.answer(f"Возникла ошибка при зачислении бонусов")
    else:
        success = await rq.set_bonus_balance(callback.from_user.id, "remove", bonus_deduction, amount, callback.from_user.id)
        if success:
            await callback.message.answer(f"Списано {bonus_deduction:.2f} бонусов пользователя {user_data.name}\n"
                                          f"Итоговая цена для клиента: {amount-bonus_deduction}")
        else:
            await callback.message.answer(f"Возникла ошибка при списании бонусов")