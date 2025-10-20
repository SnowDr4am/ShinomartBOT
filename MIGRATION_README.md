# Миграция с SQLite на PostgreSQL

Этот документ описывает процесс миграции проекта ShinomartBOT с SQLite на PostgreSQL.

## Подготовка

### 1. Убедитесь, что PostgreSQL запущен
```bash
# Проверьте, что контейнеры PostgreSQL запущены
docker ps
```

### 2. Проверьте настройки подключения
Убедитесь, что в файле `config.py` правильно настроен `ASYNC_DATABASE_URL` для PostgreSQL.

## Выполнение миграции

### Автоматическая миграция (рекомендуется)
Запустите основной скрипт миграции:

```bash
python run_migration.py
```

Этот скрипт выполнит все шаги автоматически:
1. Инициализирует PostgreSQL базу данных
2. Создаст все необходимые таблицы
3. Заполнит начальные данные (типы товаров и категории)
4. Перенесет все данные из SQLite в PostgreSQL

### Пошаговая миграция

Если нужно выполнить миграцию по шагам:

#### Шаг 1: Инициализация базы данных
```bash
python init_postgres_db.py
```

#### Шаг 2: Заполнение начальных данных
```bash
python seed_postgres_db.py
```

#### Шаг 3: Миграция данных
```bash
python migrate_data.py
```

## Структура сервисной прослойки

После миграции данные организованы в сервисную прослойку:

### `app/database/service/user.py`
- `UserService` - работа с пользователями
- `BonusService` - работа с бонусной системой
- `TransactionService` - работа с транзакциями
- `ReviewService` - работа с отзывами
- `AppointmentService` - работа с записями
- `SettingsService` - работа с настройками
- `QRCodeService` - работа с QR кодами
- `VoteService` - работа с голосованием
- `VipClientService` - работа с VIP клиентами
- `RoleHistoryService` - работа с историей ролей

### `app/database/service/item.py`
- `StatisticsService` - работа со статистикой
- `PromotionService` - работа с промо-акциями
- `ItemTypeService` - работа с типами товаров
- `CategoryService` - работа с категориями
- `ItemService` - работа с товарами

## Обновление импортов

После миграции нужно обновить импорты в handlers:

### Было:
```python
from app.database.requests import set_user, get_user_profile
from app.database.admin_requests import get_statistics
```

### Стало:
```python
from app.database.service.user import UserService, BonusService
from app.database.service.item import StatisticsService
```

### Пример использования:
```python
# Вместо
await set_user(user_id, date_today, name, phone, birthday, bonus_balance)

# Используйте
await UserService.create_user(user_id, date_today, name, phone, birthday, bonus_balance)
```

## Проверка миграции

После выполнения миграции проверьте:

1. **Подключение к PostgreSQL:**
   ```python
   from app.database.model.database import async_session
   async with async_session() as session:
       result = await session.execute("SELECT 1")
       print("✅ Подключение к PostgreSQL работает")
   ```

2. **Наличие данных:**
   ```python
   from app.database.service.user import UserService
   users_count = await UserService.get_all_users_to_txt()
   print(f"Количество пользователей: {len(users_count)}")
   ```

## Откат (если нужно)

Если нужно вернуться к SQLite:

1. Измените `ASYNC_DATABASE_URL` в `config.py` обратно на SQLite
2. Перезапустите приложение

## Поддержка

При возникновении проблем:

1. Проверьте логи миграции
2. Убедитесь, что PostgreSQL запущен и доступен
3. Проверьте права доступа к базе данных
4. Убедитесь, что все зависимости установлены

## Файлы миграции

- `run_migration.py` - основной скрипт миграции
- `init_postgres_db.py` - инициализация PostgreSQL
- `seed_postgres_db.py` - заполнение начальных данных
- `migrate_data.py` - перенос данных из SQLite
- `MIGRATION_README.md` - этот файл


