from aiogram import F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from app.handlers.main import admin_router
import app.keyboards.admin.admin as kb
import app.database.requests as rq