from aiogram.fsm.state import StatesGroup, State

class SubmitItemStates(StatesGroup):
    waiting_brand = State()
    waiting_description = State()
    waiting_price = State()
    waiting_picture = State()
    waiting_confirm = State()