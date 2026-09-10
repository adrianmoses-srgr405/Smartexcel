import logging
from typing import Any, Dict
from sqlalchemy import create_engine, text

from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.engine.url import make_url
from app.core.config import settings

logger = logging.getLogger(__name__)

def ensure_database_exists(db_url: str):
    """
    Automatically creates the target database in PostgreSQL or MySQL if it does not already exist.
    """
    try:
        url_obj = make_url(db_url)
        backend_name = url_obj.get_backend_name()

        if backend_name == "postgresql":
            target_db = url_obj.database
            maintenance_url = url_obj.set(database="postgres")
            temp_engine = create_engine(maintenance_url, isolation_level="AUTOCOMMIT")
            with temp_engine.connect() as conn:
                result = conn.execute(
                    text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
                    {"dbname": target_db}
                )
                if not result.scalar():
                    owner = url_obj.username or "postgres"
                    try:
                        conn.execute(text(f'CREATE DATABASE "{target_db}" OWNER "{owner}"'))
                    except Exception:
                        conn.execute(text(f'CREATE DATABASE "{target_db}"'))
                    logger.info(f"[Database] Created PostgreSQL database '{target_db}' successfully.")
            temp_engine.dispose()

        elif backend_name == "mysql":
            target_db = url_obj.database
            maintenance_url = url_obj.set(database="")
            temp_engine = create_engine(maintenance_url, isolation_level="AUTOCOMMIT")
            with temp_engine.connect() as conn:
                conn.execute(text(f'CREATE DATABASE IF NOT EXISTS `{target_db}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci'))
                logger.info(f"[Database] Ensured MySQL database '{target_db}' exists.")
            temp_engine.dispose()
    except Exception as e:
        logger.warning(f"[Database] Auto-create check: {e}")

# Ensure database exists before creating the engine
ensure_database_exists(settings.DATABASE_URL)

connect_args: Dict[str, Any] = {}

engine_kwargs: Dict[str, Any] = {"pool_pre_ping": True}

if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
else:
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20
    })

engine = create_engine(

    settings.DATABASE_URL,
    connect_args=connect_args,
    **engine_kwargs
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

