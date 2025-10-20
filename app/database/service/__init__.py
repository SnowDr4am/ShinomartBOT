from .user import UserService
from .bonus import BonusService
from .transaction import TransactionService
from .review import ReviewService
from .appointment import AppointmentService
from .qr_code import QRCodeService
from .vip_client import VipClientService

from .promotion import PromotionService
from .item_type import ItemTypeService
from .category import CategoryService
from .item import ItemService
from .statistic import StatisticsService
from .vote import VoteHistoryService


__all__ = [
    # Основные сервисы
    "UserService",
    "BonusService",
    "TransactionService",
    "ReviewService",
    "AppointmentService",
    "QRCodeService",
    "VipClientService",

    # Сервисы каталога
    "PromotionService",
    "ItemTypeService",
    "CategoryService",
    "ItemService",
    "StatisticsService",
    "VoteHistoryService",
]
