#!/usr/bin/env python3
"""
Скрипт для миграции данных из SQLite в PostgreSQL
"""
import asyncio
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional
import json

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text

# Импорты старых моделей (SQLite)
from app.database.models import (
    User as OldUser,
    PurchaseHistory as OldPurchaseHistory,
    UserBonusBalance as OldUserBonusBalance,
    BonusSystem as OldBonusSystem,
    RoleHistory as OldRoleHistory,
    Review as OldReview,
    Appointment as OldAppointment,
    Settings as OldSettings,
    QRCode as OldQRCode,
    VoteHistory as OldVoteHistory,
    VipClient as OldVipClient,
    Promotion as OldPromotion,
    ItemType as OldItemType,
    Category as OldCategory,
    Item as OldItem
)

# Импорты новых моделей (PostgreSQL)
from app.database.model.user import User
from app.database.model.user_bonus_balance import UserBonusBalance
from app.database.model.purchase_history import PurchaseHistory
from app.database.model.bonus_system import BonusSystem
from app.database.model.role_history import RoleHistory
from app.database.model.review import Review
from app.database.model.appointment import Appointment
from app.database.model.setting import Settings
from app.database.model.qr_codes import QRCode
from app.database.model.vote_history import VoteHistory
from app.database.model.vip_clients import VipClient
from app.database.model.promotion import Promotion
from app.database.model.item_type import ItemType
from app.database.model.categories import Category
from app.database.model.item import Item

from config import ASYNC_DATABASE_URL

# Настройка старой базы данных (SQLite)
OLD_DATABASE_URL = 'sqlite+aiosqlite:///db.sqlite3'
old_engine = create_async_engine(OLD_DATABASE_URL, echo=False)
OldAsyncSessionLocal = sessionmaker(
    bind=old_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Настройка новой базы данных (PostgreSQL)
new_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
NewAsyncSessionLocal = sessionmaker(
    bind=new_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class DataMigrator:
    """Класс для миграции данных"""
    
    def __init__(self):
        self.old_session = None
        self.new_session = None
        self.migration_stats = {
            'users': 0,
            'purchase_history': 0,
            'user_bonus_balance': 0,
            'bonus_system': 0,
            'role_history': 0,
            'reviews': 0,
            'appointments': 0,
            'settings': 0,
            'qr_codes': 0,
            'vote_history': 0,
            'vip_clients': 0,
            'promotions': 0,
            'item_types': 0,
            'categories': 0,
            'items': 0
        }

    async def __aenter__(self):
        self.old_session = OldAsyncSessionLocal()
        self.new_session = NewAsyncSessionLocal()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.old_session:
            await self.old_session.close()
        if self.new_session:
            await self.new_session.close()

    async def migrate_users(self):
        """Миграция пользователей"""
        print("🔄 Миграция пользователей...")
        
        old_users = await self.old_session.execute(select(OldUser))
        old_users_list = old_users.scalars().all()
        
        for old_user in old_users_list:
            # Проверяем, существует ли пользователь в новой БД
            existing_user = await self.new_session.scalar(
                select(User).where(User.user_id == old_user.user_id)
            )
            
            if not existing_user:
                new_user = User(
                    user_id=old_user.user_id,
                    registration_date=old_user.registration_date,
                    name=old_user.name,
                    mobile_phone=old_user.mobile_phone,
                    birthday_date=old_user.birthday_date,
                    role=old_user.role
                )
                self.new_session.add(new_user)
                self.migration_stats['users'] += 1
        
        await self.new_session.commit()
        print(f"✅ Мигрировано пользователей: {self.migration_stats['users']}")

    async def migrate_user_bonus_balance(self):
        """Миграция бонусных балансов"""
        print("🔄 Миграция бонусных балансов...")
        
        old_balances = await self.old_session.execute(select(OldUserBonusBalance))
        old_balances_list = old_balances.scalars().all()
        
        for old_balance in old_balances_list:
            # Проверяем, существует ли баланс в новой БД
            existing_balance = await self.new_session.scalar(
                select(UserBonusBalance).where(UserBonusBalance.user_id == old_balance.user_id)
            )
            
            if not existing_balance:
                new_balance = UserBonusBalance(
                    user_id=old_balance.user_id,
                    balance=old_balance.balance
                )
                self.new_session.add(new_balance)
                self.migration_stats['user_bonus_balance'] += 1
        
        await self.new_session.commit()
        print(f"✅ Мигрировано бонусных балансов: {self.migration_stats['user_bonus_balance']}")

    async def migrate_purchase_history(self):
        """Миграция истории покупок"""
        print("🔄 Миграция истории покупок...")
        
        old_transactions = await self.old_session.execute(select(OldPurchaseHistory))
        old_transactions_list = old_transactions.scalars().all()
        
        for old_transaction in old_transactions_list:
            # Проверяем, существует ли транзакция в новой БД
            existing_transaction = await self.new_session.scalar(
                select(PurchaseHistory).where(
                    PurchaseHistory.user_id == old_transaction.user_id,
                    PurchaseHistory.worker_id == old_transaction.worker_id,
                    PurchaseHistory.transaction_date == old_transaction.transaction_date,
                    PurchaseHistory.amount == old_transaction.amount
                )
            )
            
            if not existing_transaction:
                new_transaction = PurchaseHistory(
                    user_id=old_transaction.user_id,
                    worker_id=old_transaction.worker_id,
                    transaction_date=old_transaction.transaction_date,
                    transaction_type=old_transaction.transaction_type,
                    amount=old_transaction.amount,
                    bonus_amount=old_transaction.bonus_amount
                )
                self.new_session.add(new_transaction)
                self.migration_stats['purchase_history'] += 1
        
        await self.new_session.commit()
        print(f"✅ Мигрировано транзакций: {self.migration_stats['purchase_history']}")

    async def migrate_bonus_system(self):
        """Миграция настроек бонусной системы"""
        print("🔄 Миграция настроек бонусной системы...")
        
        old_bonus_settings = await self.old_session.execute(select(OldBonusSystem))
        old_bonus_settings_list = old_bonus_settings.scalars().all()
        
        for old_setting in old_bonus_settings_list:
            # Проверяем, существует ли настройка в новой БД
            existing_setting = await self.new_session.scalar(
                select(BonusSystem).where(BonusSystem.id == old_setting.id)
            )
            
            if not existing_setting:
                new_setting = BonusSystem(
                    id=old_setting.id,
                    cashback=old_setting.cashback,
                    max_debit=old_setting.max_debit,
                    start_bonus_balance=old_setting.start_bonus_balance,
                    voting_bonus=old_setting.voting_bonus,
                    vip_cashback=old_setting.vip_cashback
                )
                self.new_session.add(new_setting)
                self.migration_stats['bonus_system'] += 1
        
        await self.new_session.commit()
        print(f"✅ Мигрировано настроек бонусной системы: {self.migration_stats['bonus_system']}")

    async def migrate_role_history(self):
        """Миграция истории ролей"""
        print("🔄 Миграция истории ролей...")
        
        old_role_history = await self.old_session.execute(select(OldRoleHistory))
        old_role_history_list = old_role_history.scalars().all()
        
        for old_role in old_role_history_list:
            # Проверяем, существует ли запись в новой БД
            existing_role = await self.new_session.scalar(
                select(RoleHistory).where(
                    RoleHistory.admin_id == old_role.admin_id,
                    RoleHistory.user_id == old_role.user_id,
                    RoleHistory.role == old_role.role,
                    RoleHistory.assigned_date == old_role.assigned_date
                )
            )
            
            if not existing_role:
                new_role = RoleHistory(
                    admin_id=old_role.admin_id,
                    user_id=old_role.user_id,
                    role=old_role.role,
                    assigned_date=old_role.assigned_date
                )
                self.new_session.add(new_role)
                self.migration_stats['role_history'] += 1
        
        await self.new_session.commit()
        print(f"✅ Мигрировано записей истории ролей: {self.migration_stats['role_history']}")

    async def migrate_reviews(self):
        """Миграция отзывов"""
        print("🔄 Миграция отзывов...")
        
        old_reviews = await self.old_session.execute(select(OldReview))
        old_reviews_list = old_reviews.scalars().all()
        
        for old_review in old_reviews_list:
            # Проверяем, существует ли отзыв в новой БД
            existing_review = await self.new_session.scalar(
                select(Review).where(
                    Review.user_id == old_review.user_id,
                    Review.purchase_id == old_review.purchase_id,
                    Review.worker_id == old_review.worker_id,
                    Review.review_date == old_review.review_date
                )
            )
            
            if not existing_review:
                new_review = Review(
                    user_id=old_review.user_id,
                    purchase_id=old_review.purchase_id,
                    worker_id=old_review.worker_id,
                    review_date=old_review.review_date,
                    rating=old_review.rating,
                    comment=old_review.comment
                )
                self.new_session.add(new_review)
                self.migration_stats['reviews'] += 1
        
        await self.new_session.commit()
        print(f"✅ Мигрировано отзывов: {self.migration_stats['reviews']}")

    async def migrate_appointments(self):
        """Миграция записей"""
        print("🔄 Миграция записей...")
        
        old_appointments = await self.old_session.execute(select(OldAppointment))
        old_appointments_list = old_appointments.scalars().all()
        
        for old_appointment in old_appointments_list:
            # Проверяем, существует ли запись в новой БД
            existing_appointment = await self.new_session.scalar(
                select(Appointment).where(
                    Appointment.user_id == old_appointment.user_id,
                    Appointment.mobile_phone == old_appointment.mobile_phone,
                    Appointment.date_time == old_appointment.date_time,
                    Appointment.service == old_appointment.service
                )
            )
            
            if not existing_appointment:
                new_appointment = Appointment(
                    user_id=old_appointment.user_id,
                    mobile_phone=old_appointment.mobile_phone,
                    date_time=old_appointment.date_time,
                    service=old_appointment.service,
                    is_confirmed=old_appointment.is_confirmed,
                    is_notified=old_appointment.is_notified
                )
                self.new_session.add(new_appointment)
                self.migration_stats['appointments'] += 1
        
        await self.new_session.commit()
        print(f"✅ Мигрировано записей: {self.migration_stats['appointments']}")

    async def migrate_settings(self):
        """Миграция настроек"""
        print("🔄 Миграция настроек...")
        
        old_settings = await self.old_session.execute(select(OldSettings))
        old_settings_list = old_settings.scalars().all()
        
        for old_setting in old_settings_list:
            # Проверяем, существует ли настройка в новой БД
            existing_setting = await self.new_session.scalar(
                select(Settings).where(Settings.id == old_setting.id)
            )
            
            if not existing_setting:
                new_setting = Settings(
                    id=old_setting.id,
                    daily_message_id=old_setting.daily_message_id
                )
                self.new_session.add(new_setting)
                self.migration_stats['settings'] += 1
        
        await self.new_session.commit()
        print(f"✅ Мигрировано настроек: {self.migration_stats['settings']}")

    async def migrate_qr_codes(self):
        """Миграция QR кодов"""
        print("🔄 Миграция QR кодов...")
        
        old_qr_codes = await self.old_session.execute(select(OldQRCode))
        old_qr_codes_list = old_qr_codes.scalars().all()
        
        for old_qr in old_qr_codes_list:
            # Проверяем, существует ли QR код в новой БД
            existing_qr = await self.new_session.scalar(
                select(QRCode).where(
                    QRCode.user_id == old_qr.user_id,
                    QRCode.phone_number == old_qr.phone_number,
                    QRCode.created_at == old_qr.created_at
                )
            )
            
            if not existing_qr:
                new_qr = QRCode(
                    user_id=old_qr.user_id,
                    phone_number=old_qr.phone_number,
                    created_at=old_qr.created_at
                )
                self.new_session.add(new_qr)
                self.migration_stats['qr_codes'] += 1
        
        await self.new_session.commit()
        print(f"✅ Мигрировано QR кодов: {self.migration_stats['qr_codes']}")

    async def migrate_vote_history(self):
        """Миграция истории голосований"""
        print("🔄 Миграция истории голосований...")
        
        old_vote_history = await self.old_session.execute(select(OldVoteHistory))
        old_vote_history_list = old_vote_history.scalars().all()
        
        for old_vote in old_vote_history_list:
            # Проверяем, существует ли запись в новой БД
            existing_vote = await self.new_session.scalar(
                select(VoteHistory).where(
                    VoteHistory.user_id == old_vote.user_id,
                    VoteHistory.data == old_vote.data
                )
            )
            
            if not existing_vote:
                new_vote = VoteHistory(
                    user_id=old_vote.user_id,
                    data=old_vote.data
                )
                self.new_session.add(new_vote)
                self.migration_stats['vote_history'] += 1
        
        await self.new_session.commit()
        print(f"✅ Мигрировано записей истории голосований: {self.migration_stats['vote_history']}")

    async def migrate_vip_clients(self):
        """Миграция VIP клиентов"""
        print("🔄 Миграция VIP клиентов...")
        
        old_vip_clients = await self.old_session.execute(select(OldVipClient))
        old_vip_clients_list = old_vip_clients.scalars().all()
        
        for old_vip in old_vip_clients_list:
            # Проверяем, существует ли VIP клиент в новой БД
            existing_vip = await self.new_session.scalar(
                select(VipClient).where(VipClient.user_id == old_vip.user_id)
            )
            
            if not existing_vip:
                new_vip = VipClient(user_id=old_vip.user_id)
                self.new_session.add(new_vip)
                self.migration_stats['vip_clients'] += 1
        
        await self.new_session.commit()
        print(f"✅ Мигрировано VIP клиентов: {self.migration_stats['vip_clients']}")

    async def migrate_promotions(self):
        """Миграция промо-акций"""
        print("🔄 Миграция промо-акций...")
        
        old_promotions = await self.old_session.execute(select(OldPromotion))
        old_promotions_list = old_promotions.scalars().all()
        
        for old_promo in old_promotions_list:
            # Проверяем, существует ли промо в новой БД
            existing_promo = await self.new_session.scalar(
                select(Promotion).where(Promotion.id == old_promo.id)
            )
            
            if not existing_promo:
                new_promo = Promotion(
                    id=old_promo.id,
                    short_description=old_promo.short_description,
                    full_description=old_promo.full_description,
                    image_path=old_promo.image_path,
                    created_ad=old_promo.created_ad,
                    is_active=old_promo.is_active
                )
                self.new_session.add(new_promo)
                self.migration_stats['promotions'] += 1
        
        await self.new_session.commit()
        print(f"✅ Мигрировано промо-акций: {self.migration_stats['promotions']}")

    async def migrate_item_types(self):
        """Миграция типов товаров"""
        print("🔄 Миграция типов товаров...")
        
        old_item_types = await self.old_session.execute(select(OldItemType))
        old_item_types_list = old_item_types.scalars().all()
        
        for old_item_type in old_item_types_list:
            # Проверяем, существует ли тип товара в новой БД
            existing_item_type = await self.new_session.scalar(
                select(ItemType).where(ItemType.id == old_item_type.id)
            )
            
            if not existing_item_type:
                new_item_type = ItemType(
                    id=old_item_type.id,
                    value=old_item_type.value
                )
                self.new_session.add(new_item_type)
                self.migration_stats['item_types'] += 1
        
        await self.new_session.commit()
        print(f"✅ Мигрировано типов товаров: {self.migration_stats['item_types']}")

    async def migrate_categories(self):
        """Миграция категорий"""
        print("🔄 Миграция категорий...")
        
        old_categories = await self.old_session.execute(select(OldCategory))
        old_categories_list = old_categories.scalars().all()
        
        for old_category in old_categories_list:
            # Проверяем, существует ли категория в новой БД
            existing_category = await self.new_session.scalar(
                select(Category).where(Category.id == old_category.id)
            )
            
            if not existing_category:
                new_category = Category(
                    id=old_category.id,
                    value=old_category.value,
                    type_id=old_category.type_id
                )
                self.new_session.add(new_category)
                self.migration_stats['categories'] += 1
        
        await self.new_session.commit()
        print(f"✅ Мигрировано категорий: {self.migration_stats['categories']}")

    async def migrate_items(self):
        """Миграция товаров"""
        print("🔄 Миграция товаров...")
        
        old_items = await self.old_session.execute(select(OldItem))
        old_items_list = old_items.scalars().all()
        
        for old_item in old_items_list:
            # Проверяем, существует ли товар в новой БД
            existing_item = await self.new_session.scalar(
                select(Item).where(Item.id == old_item.id)
            )
            
            if not existing_item:
                new_item = Item(
                    id=old_item.id,
                    category_id=old_item.category_id,
                    value=old_item.value,
                    meta_data=old_item.meta_data
                )
                self.new_session.add(new_item)
                self.migration_stats['items'] += 1
        
        await self.new_session.commit()
        print(f"✅ Мигрировано товаров: {self.migration_stats['items']}")

    async def run_migration(self):
        """Запуск полной миграции"""
        print("🚀 Начинаем миграцию данных из SQLite в PostgreSQL...")
        print("=" * 60)
        
        try:
            # Миграция в правильном порядке (с учетом зависимостей)
            await self.migrate_users()
            await self.migrate_user_bonus_balance()
            await self.migrate_purchase_history()
            await self.migrate_bonus_system()
            await self.migrate_role_history()
            await self.migrate_reviews()
            await self.migrate_appointments()
            await self.migrate_settings()
            await self.migrate_qr_codes()
            await self.migrate_vote_history()
            await self.migrate_vip_clients()
            await self.migrate_promotions()
            await self.migrate_item_types()
            await self.migrate_categories()
            await self.migrate_items()
            
            print("=" * 60)
            print("🎉 Миграция завершена успешно!")
            print("\n📊 Статистика миграции:")
            for table, count in self.migration_stats.items():
                print(f"  {table}: {count} записей")
            
            total_records = sum(self.migration_stats.values())
            print(f"\n📈 Всего мигрировано записей: {total_records}")
            
        except Exception as e:
            print(f"❌ Ошибка во время миграции: {e}")
            await self.new_session.rollback()
            raise


async def main():
    """Основная функция"""
    print("🔄 Инициализация миграции...")
    
    async with DataMigrator() as migrator:
        await migrator.run_migration()


if __name__ == "__main__":
    asyncio.run(main())


