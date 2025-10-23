from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def generate_cells_keyboard(cells: list, page: int = 1) -> InlineKeyboardMarkup:
    """Генерация клавиатуры 10x10 для ячеек"""
    cells_per_page = 100  # 10x10
    keyboard = []
    
    total_cells = len(cells)
    total_pages = (total_cells + cells_per_page - 1) // cells_per_page if total_cells > 0 else 1
    
    start = (page - 1) * cells_per_page
    end = start + cells_per_page
    cells_on_page = cells[start:end] if cells else []
    
    # Генерируем 10 рядов по 10 кнопок
    for row in range(10):
        row_buttons = []
        for col in range(10):
            cell_index = start + row * 10 + col
            
            if cell_index < len(cells):
                cell = cells[cell_index]
                # Проверяем, занята ли ячейка
                if cell.cell_storage:
                    button_text = f"✅ {cell.id}"
                else:
                    button_text = f"{cell.id}"
                callback_data = f"storage_cell:{cell.id}"
            else:
                # Пустая кнопка
                button_text = "·"
                callback_data = "ignore"
            
            row_buttons.append(InlineKeyboardButton(text=button_text, callback_data=callback_data))
        keyboard.append(row_buttons)
    
    # Добавляем пагинацию, если нужно
    if total_pages > 1:
        pagination_buttons = []
        if page > 1:
            pagination_buttons.append(
                InlineKeyboardButton(text="⬅️ Назад", callback_data=f"storage_page:{page-1}")
            )
        pagination_buttons.append(
            InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="ignore")
        )
        if page < total_pages:
            pagination_buttons.append(
                InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"storage_page:{page+1}")
            )
        keyboard.append(pagination_buttons)
    
    # Кнопка назад
    keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="storage_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def build_empty_cell(cell_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Заполнить ячейку", callback_data=f"start_add_cell_data:{cell_id}")],
        [InlineKeyboardButton(text="Назад", callback_data="storage_open_cells")]
    ])

def get_filled_cell_keyboard(cell_id: int) -> InlineKeyboardMarkup:
    """Эстетичная и удобная клавиатура для заполненной ячейки"""
    keyboard = [
        [
            InlineKeyboardButton(text="📄 Открыть документ", callback_data=f"storage_generate_word:{cell_id}"),
        ],
        [
            InlineKeyboardButton(text="📅 Продлить хранение", callback_data=f"storage_extend:{cell_id}"),
            InlineKeyboardButton(text="🔓 Освободить", callback_data=f"storage_free:{cell_id}"),
        ],
        [
            InlineKeyboardButton(text="🗑️ Удалить ячейку", callback_data=f"storage_delete:{cell_id}")
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="storage_open_cells")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)