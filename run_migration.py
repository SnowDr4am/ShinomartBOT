#!/usr/bin/env python3
"""
Основной скрипт для запуска полной миграции с SQLite на PostgreSQL
"""
import asyncio
import sys
import os

# Добавляем корневую директорию проекта в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from init_postgres_db import init_database
from seed_postgres_db import seed_initial_data
from migrate_data import DataMigrator


async def run_full_migration():
    """Запуск полной миграции"""
    print("🚀 ЗАПУСК ПОЛНОЙ МИГРАЦИИ С SQLITE НА POSTGRESQL")
    print("=" * 60)
    
    try:
        # Шаг 1: Инициализация новой базы данных
        print("\n📋 ШАГ 1: Инициализация PostgreSQL базы данных")
        print("-" * 50)
        await init_database()
        
        # Шаг 2: Заполнение начальных данных
        print("\n📋 ШАГ 2: Заполнение начальных данных")
        print("-" * 50)
        await seed_initial_data()
        
        # Шаг 3: Миграция данных
        print("\n📋 ШАГ 3: Миграция данных из SQLite")
        print("-" * 50)
        async with DataMigrator() as migrator:
            await migrator.run_migration()
        
        print("\n" + "=" * 60)
        print("🎉 МИГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
        print("✅ База данных PostgreSQL готова к использованию")
        print("✅ Все данные перенесены из SQLite")
        print("✅ Начальные данные заполнены")
        print("\n💡 Теперь можно обновить импорты в handlers для использования новых сервисов")
        
    except Exception as e:
        print(f"\n❌ ОШИБКА ВО ВРЕМЯ МИГРАЦИИ: {e}")
        print("🔄 Проверьте настройки подключения к PostgreSQL")
        sys.exit(1)


async def main():
    """Основная функция"""
    await run_full_migration()


if __name__ == "__main__":
    asyncio.run(main())


