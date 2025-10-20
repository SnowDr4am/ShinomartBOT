#!/usr/bin/env python3
"""
Скрипт для инициализации PostgreSQL базы данных
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

from app.database.model.database import Base
from config import ASYNC_DATABASE_URL


async def init_database():
    """Инициализация базы данных"""
    print("🔄 Инициализация PostgreSQL базы данных...")
    
    engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
    
    try:
        async with engine.begin() as conn:
            # Создаем все таблицы
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Таблицы созданы успешно!")
            
            # Проверяем созданные таблицы
            result = await conn.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            )
            tables = result.fetchall()
            
            print(f"\n📋 Созданные таблицы ({len(tables)}):")
            for table in tables:
                print(f"  - {table[0]}")
                
    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")
        raise
    finally:
        await engine.dispose()
    
    print("\n🎉 База данных PostgreSQL готова к использованию!")


async def main():
    """Основная функция"""
    await init_database()


if __name__ == "__main__":
    asyncio.run(main())


