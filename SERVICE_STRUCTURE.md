# Структура сервисной прослойки

## 📁 Организация файлов

Сервисы разбиты по логическим группам в папке `app/database/service/`:

### 👤 Пользователи и связанные сервисы
- **`user.py`** - `UserService` - работа с пользователями, ролями, профилями
- **`bonus.py`** - `BonusService` - бонусная система и балансы
- **`transaction.py`** - `TransactionService` - история транзакций и отчеты
- **`review.py`** - `ReviewService` - отзывы и оценки
- **`appointment.py`** - `AppointmentService` - записи и уведомления
- **`settings.py`** - `SettingsService` - системные настройки
- **`qr_code.py`** - `QRCodeService` - QR коды
- **`vote.py`** - `VoteService` - голосования
- **`vip_client.py`** - `VipClientService` - VIP клиенты
- **`role_history.py`** - `RoleHistoryService` - история ролей

### 📦 Каталог и статистика
- **`item.py`** - содержит 5 сервисов:
  - `StatisticsService` - общая статистика и отчеты
  - `PromotionService` - промо-акции
  - `ItemTypeService` - типы товаров
  - `CategoryService` - категории товаров
  - `ItemService` - товары

## 🔄 Импорт сервисов

### Вариант 1: Импорт конкретного сервиса
```python
from app.database.service.user import UserService
from app.database.service.bonus import BonusService
```

### Вариант 2: Импорт через __init__.py
```python
from app.database.service import UserService, BonusService, StatisticsService
```

### Вариант 3: Импорт всех сервисов
```python
from app.database.service import *
```

## 📋 Примеры использования

### Работа с пользователями
```python
from app.database.service import UserService

# Создание пользователя
await UserService.create_user(
    user_id="123456789",
    date_today=datetime.now(),
    name="Иван Иванов",
    mobile_phone="+7900123456",
    birthday=date(1990, 1, 1),
    bonus_balance=500.0
)

# Получение профиля
profile = await UserService.get_user_profile("123456789")
```

### Работа с бонусами
```python
from app.database.service import BonusService

# Получение баланса
balance = await BonusService.get_bonus_balance("123456789")

# Изменение баланса
await BonusService.set_bonus_balance(
    user_id="123456789",
    action="add",
    amount_bonus=100.0,
    amount_cell=1000.0,
    worker_id="987654321"
)
```

### Работа со статистикой
```python
from app.database.service import StatisticsService

# Общая статистика
stats = await StatisticsService.get_statistics("month")

# Статистика работника
worker_stats = await StatisticsService.get_worker_statistics("987654321", "week")
```

## 🎯 Преимущества новой структуры

1. **Модульность** - каждый сервис отвечает за свою область
2. **Читаемость** - легко найти нужный функционал
3. **Масштабируемость** - просто добавлять новые сервисы
4. **Переиспользование** - сервисы можно использовать в разных частях приложения
5. **Тестируемость** - каждый сервис можно тестировать отдельно

## 🔧 Миграция с старых импортов

### Было:
```python
from app.database.requests import set_user, get_user_profile
from app.database.admin_requests import get_statistics
```

### Стало:
```python
from app.database.service import UserService, StatisticsService

# Вместо set_user() -> UserService.create_user()
# Вместо get_user_profile() -> UserService.get_user_profile()
# Вместо get_statistics() -> StatisticsService.get_statistics()
```


