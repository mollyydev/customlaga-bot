from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from custom.config import (
    CUSTOMIZATION_DB_KEY,
    CUSTOMIZATION_FILE_PATH,
    CustomizationConfig,
    PageConfig,
)


logger = structlog.get_logger(__name__)


class CustomizationService:
    """Центральный сервис кастомизации интерфейса бота.

    Обеспечивает:
    - Синхронизацию конфигурации между PostgreSQL и файлом data/customization.json
    - Быстрый доступ из оперативной памяти к активной конфигурации
    - Real-time режим при внесении правок пользователем
    - Приоритет кастомных страниц, кнопок и текстов над встроенными
    """

    _cache: CustomizationConfig | None = None
    _lock: asyncio.Lock = asyncio.Lock()
    _db_synced: bool = False

    def is_enabled(self) -> bool:
        """Проверяет, включена ли кастомизация бота."""
        if self._cache is None:
            # Try to read directly from json file if cache not yet populated
            if CUSTOMIZATION_FILE_PATH.exists():
                try:
                    self._cache = CustomizationConfig.from_json(
                        CUSTOMIZATION_FILE_PATH.read_text(encoding="utf-8")
                    )
                except Exception:
                    pass
        return bool(self._cache and self._cache.enabled)

    def get_cached_config(self) -> CustomizationConfig:
        """Возвращает текущую конфигурацию из памяти или дефолтную."""
        if self._cache is not None:
            return self._cache
        if CUSTOMIZATION_FILE_PATH.exists():
            try:
                self._cache = CustomizationConfig.from_json(
                    CUSTOMIZATION_FILE_PATH.read_text(encoding="utf-8")
                )
                return self._cache
            except Exception as e:
                logger.warning("Не удалось прочитать customization.json", error=str(e))
        self._cache = CustomizationConfig()
        return self._cache

    async def get_config(self, db: AsyncSession | None = None) -> CustomizationConfig:
        """Получает конфигурацию.

        Если кэш уже в памяти — отдает его.
        Если кэша нет — проверяет БД, синхронизирует с JSON файлом и загружает в память.
        """
        if self._cache is not None:
            return self._cache

        async with self._lock:
            if self._cache is not None:
                return self._cache

            # 1. Попытка загрузить из БД
            db_config = None
            if db is not None:
                db_config = await self._load_from_db(db)

            # 2. Если в БД есть запись, проверяем файл
            if db_config is not None:
                self._cache = db_config
                await self._ensure_disk_file_synced(db_config)
                self._db_synced = True
                return self._cache

            # 3. Если в БД нет, проверяем JSON-файл
            if CUSTOMIZATION_FILE_PATH.exists():
                try:
                    content = CUSTOMIZATION_FILE_PATH.read_text(encoding="utf-8")
                    self._cache = CustomizationConfig.from_json(content)
                    if db is not None:
                        await self._save_to_db(db, self._cache)
                    return self._cache
                except Exception as e:
                    logger.warning("Ошибка чтения файла кастомизации", error=str(e))

            # 4. Инициализация дефолтной конфигурации
            self._cache = CustomizationConfig()
            await self._ensure_disk_file_synced(self._cache)
            if db is not None:
                await self._save_to_db(db, self._cache)

            return self._cache

    async def update_config(
        self, db: AsyncSession | None, new_data: dict[str, Any]
    ) -> CustomizationConfig:
        """Обновляет конфигурацию в реальном времени.

        - Немедленно обновляет конфигурацию в памяти (real-time режим для бота)
        - Сохраняет изменения в PostgreSQL
        - Устанавливает флаг needs_restart=True (предупреждение в UI)
        """
        async with self._lock:
            current = self.get_cached_config()
            merged_dict = current.to_dict()
            merged_dict.update(new_data)
            merged_dict["needs_restart"] = True
            merged_dict["realtime_mode"] = True

            updated_config = CustomizationConfig.from_dict(merged_dict)
            self._cache = updated_config

            if db is not None:
                await self._save_to_db(db, updated_config)

            logger.info(
                "Кастомизация обновлена в реальном времени",
                enabled=updated_config.enabled,
                needs_restart=updated_config.needs_restart,
            )
            return updated_config

    async def sync_to_disk(self) -> None:
        """Синхронизирует текущую конфигурацию из памяти в файл JSON на диске.

        Сбрасывает предупреждение needs_restart.
        """
        async with self._lock:
            config = self.get_cached_config()
            config.needs_restart = False
            config.realtime_mode = False
            await self._ensure_disk_file_synced(config)
            self._cache = config
            logger.info("Конфигурация кастомизации синхронизирована с файлом на диске")

    async def _ensure_disk_file_synced(self, config: CustomizationConfig) -> None:
        """Записывает конфигурацию в JSON-файл."""
        try:
            CUSTOMIZATION_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
            CUSTOMIZATION_FILE_PATH.write_text(config.to_json(), encoding="utf-8")
        except Exception as e:
            logger.error("Не удалось записать customization.json", error=str(e))

    async def _load_from_db(self, db: AsyncSession) -> CustomizationConfig | None:
        try:
            from app.database.models import SystemSetting

            query = select(SystemSetting).where(SystemSetting.key == CUSTOMIZATION_DB_KEY)
            result = await db.execute(query)
            setting = result.scalar_one_or_none()
            if setting and setting.value:
                return CustomizationConfig.from_json(setting.value)
        except Exception as e:
            logger.warning("Не удалось загрузить кастомизацию из БД", error=str(e))
        return None

    async def _save_to_db(self, db: AsyncSession, config: CustomizationConfig) -> None:
        try:
            from app.database.crud.system_setting import upsert_system_setting

            await upsert_system_setting(
                db=db,
                key=CUSTOMIZATION_DB_KEY,
                value=config.to_json(),
                description="Настройки кастомизации интерфейса бота (customlaga)",
            )
            await db.commit()
        except Exception as e:
            logger.error("Не удалось сохранить кастомизацию в БД", error=str(e))

    def get_page(self, page_id: str) -> PageConfig | None:
        """Получает конфигурацию страницы по ее идентификатору."""
        config = self.get_cached_config()
        return config.pages.get(page_id)


customization_service = CustomizationService()
