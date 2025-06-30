from aiogram.fsm.state import StatesGroup, State

class SubmitItemStates(StatesGroup):
    waiting_brand = State()
    waiting_params = State()
    waiting_description = State()
    waiting_amount = State()
    waiting_price = State()
    waiting_picture = State()

class CreateItemStates(StatesGroup):
    waiting_brand = State()
    waiting_params = State()
    waiting_description = State()
    waiting_amount = State()
    waiting_purchase_price = State()
    waiting_price = State()
    waiting_picture = State()

class EditItemStates(StatesGroup):
    waiting_field_input = State()
    waiting_photos = State()