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


@user_router.message(CommandStart())
async def cmd_start(message: Message):
    if not await rq.check_user_by_id(message.from_user.id):
        await message.answer(
            "<b>Привет!</b>\n\n"
            "Я бот шиномарта, который любит злить бухгалтера и делать для Вас скидки\n\n"
            "Для начала сотрудничества с нами, Вам необходимо зарегистрироваться",
            parse_mode="HTML",
            reply_markup=kb.registration
        )
    else:
        await message.answer(
            "<b>Привет!</b>\n\n"
            "Я бот шиномарта, который любит злить бухгалтера и делать для Вас скидки\n"
            "Вы находитесь в основном меню",
            parse_mode='HTML',
            reply_markup=kb.main_menu
        )







