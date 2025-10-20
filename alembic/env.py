import os
import sys
import asyncio
import datetime
import shutil
import subprocess
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from dotenv import load_dotenv

load_dotenv()

# --- ЛОГИ ---
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- URL БД (ASYNC) ---
ASYNC_DB_URL = os.getenv("ASYNC_DATABASE_URL")
if not ASYNC_DB_URL:
    raise RuntimeError("ASYNC_DATABASE_URL is not set")
config.set_main_option("sqlalchemy.url", ASYNC_DB_URL)

# --- Импорт моделей и metadata ---
sys.path.append(os.getcwd())
from app.database.model import Base  # подставь свой пакет, если отличается
target_metadata = Base.metadata

# --- Настройки бэкапа ---
BACKUP_DIR = os.path.join(os.getcwd(), "backups")

def ensure_backup_dir():
    os.makedirs(BACKUP_DIR, exist_ok=True)

def to_sync_url(async_url: str) -> str:
    """Преобразуем postgresql+asyncpg://... -> postgresql://... для pg_dump."""
    return async_url.replace("postgresql+asyncpg://", "postgresql://")

def pg_dump_available() -> bool:
    """Проверяем, доступен ли pg_dump в PATH."""
    return shutil.which("pg_dump") is not None

def make_backup(async_url: str) -> None:
    """Создать бинарный бэкап (-Fc) в backups/ перед миграцией."""
    if not pg_dump_available():
        print("[alembic] WARN: pg_dump not found in PATH — skipping backup.")
        return

    ensure_backup_dir()
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = os.path.join(BACKUP_DIR, f"db_{ts}.dump")

    sync_url = to_sync_url(async_url)
    cmd = ["pg_dump", "-Fc", "-f", out_file, sync_url]

    print(f"[alembic] Creating backup: {out_file}")
    try:
        subprocess.run(cmd, check=True)
        print(f"[alembic] Backup created: {out_file}")
    except subprocess.CalledProcessError as e:
        # Не роняем миграции, но предупреждаем
        print(f"[alembic] WARN: backup failed: {e}. Continuing without backup.")

# --- OFFLINE режим (без подключения) ---
def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        # Бэкап в оффлайне не делаем (нет соединения)
        context.run_migrations()

# --- ONLINE режим (с подключением к БД) ---
def _detect_cmd() -> str:
    cmd_opts = getattr(config, "cmd_opts", None)
    if cmd_opts is not None and hasattr(cmd_opts, "cmd"):
        cmd = cmd_opts.cmd
        # Нормализация: берём первое слово команды
        if isinstance(cmd, (list, tuple)):
            return cmd[0] if cmd else ""
        if isinstance(cmd, str):
            return cmd

    # Фолбэк по argv (alembic revision --autogenerate ...)
    for token in sys.argv[1:4]:
        if token in {"upgrade", "downgrade", "revision", "history",
                     "current", "heads", "branches", "show", "check"}:
            return token
    return ""


async def run_migrations_online():
    alembic_cmd = _detect_cmd()   # <-- просто сохраняем, НИЧЕГО не возвращаем отсюда

    # (опционально) бэкап только для upgrade/downgrade
    if alembic_cmd in {"upgrade", "downgrade"}:
        try:
            make_backup(ASYNC_DB_URL)
        except Exception as e:
            # не заваливай миграцию из-за бэкапа, но залогируй
            print(f"[alembic] Backup warning: {e}")

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

# --- Запуск ---
if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
