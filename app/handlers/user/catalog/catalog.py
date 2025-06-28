from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message
from app.handlers.main import user_router, admin_router
from app.handlers.user.user import cmd_start
import app.keyboards.user.user as kb
import app.database.requests as rq
import app.database.ItemService as ItemService
import app.keyboards.user.catalog as catalog_kb

from .utils import *


@user_router.callback_query(F.data.startswith("catalog"))
async def view_catalog(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    category, type_id = await get_category(callback.data.split(":")[1])

    category_data = await ItemService.get_all_categories_with_items(type_id)
    await state.update_data(category=category, type_id=type_id)

    keyboard = await catalog_kb.get_catalog_keyboard(category_data, type_id)

    await callback.message.edit_text(
        f"<b>🔍 {category} — Выбор по диаметру</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"Здесь вы можете выбрать нужный размер и посмотреть актуальные товары в наличии.\n\n"
        f"👇 Нажмите на подходящий диаметр ниже:",
        parse_mode='HTML',
        reply_markup=keyboard
    )


@user_router.callback_query(F.data.startswith("category:"))
async def handle_category_by_id(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    parts = callback.data.split(":")
    category_id = int(parts[1])
    page = 1
    if len(parts) == 4 and parts[2] == "page":
        page = int(parts[3])

    items = await ItemService.get_items_by_category(category_id)
    data = await state.get_data()
    category = data.get("category")
    type_id = data.get("type_id")

    keyboard = await catalog_kb.get_item_keyboard(items, category_id, type_id, page=page)

    await callback.message.edit_text(
        text=(
            f"<b>🔍 {category} — Выбор по бренду</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"Предоставляем актуальный ассортимент\n\n"
            f"👇 Нажмите на подходящий бренд ниже:"
        ),
        parse_mode='HTML',
        reply_markup=keyboard
    )


@user_router.callback_query(F.data == "ignore")
async def ignore_handler(callback: CallbackQuery):
    await callback.answer()
