from __future__ import annotations

import os
from typing import Any

import structlog
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from custom.config import MediaType
from custom.handlers.admin_customization import register_handlers as register_admin_customization_handlers
from custom.handlers.custom_page_handler import (
    build_custom_inline_keyboard,
    register_handlers as register_custom_page_handlers,
)
from custom.services.customization_service import customization_service
from custom.services.language_service import detect_user_language
from custom.services.notification_service import format_custom_notification
from custom.services.start_flow_service import get_custom_start_messages


logger = structlog.get_logger(__name__)


async def setup_customization(dp: Dispatcher, bot: Bot | None = None) -> None:
    """Инициализация модулей кастомизации и регистрация обработчиков."""
    register_admin_customization_handlers(dp)
    register_custom_page_handlers(dp)
    
    # Предзагрузка конфигурации в память
    customization_service.get_cached_config()
    logger.info("🎨 Модуль кастомизации (customlaga) успешно инициализирован")


async def try_handle_custom_start(
    message: types.Message,
    state: FSMContext,
    db: AsyncSession,
    user: User | None = None,
    is_first_time: bool = False,
    extra_context: dict[str, Any] | None = None,
) -> bool:
    """Обрабатывает команду /start с учетом кастомных сценариев и автоопределения языка.

    Возвращает True, если сообщение было обработано кастомным сценарием.
    Возвращает False, если кастомизация выключена (делегирует стандартному поведению).
    """
    if not customization_service.is_enabled():
        return False

    config = customization_service.get_cached_config()

    # 1. Автоопределение языка
    language = "ru"
    if user and user.language:
        language = user.language
    elif config.auto_detect_language and message.from_user:
        detected = detect_user_language(
            message.from_user.language_code, default_lang=config.default_language
        )
        language = detected
        data = await state.get_data() or {}
        data["language"] = detected
        await state.set_data(data)

    user_name = (user.full_name if user else None) or (message.from_user.full_name if message.from_user else "")

    # 2. Получение сообщений по сценарию
    messages_to_send = get_custom_start_messages(
        config=config,
        user_name=user_name,
        language=language,
        is_first_time=is_first_time,
        extra_context=extra_context,
    )

    if not messages_to_send:
        return False

    bot = message.bot
    chat_id = message.chat.id

    for msg_data in messages_to_send:
        text = msg_data["text"]
        media_type = msg_data["media_type"]
        media_url = msg_data["media_url"].strip()
        buttons = msg_data["buttons"]

        keyboard = build_custom_inline_keyboard(buttons, language=language)

        media_input = None
        if media_url:
            if os.path.exists(media_url):
                media_input = FSInputFile(media_url)
            else:
                media_input = media_url

        try:
            if media_type == MediaType.PHOTO and media_input:
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=media_input,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML,
                )
            elif media_type == MediaType.VIDEO and media_input:
                await bot.send_video(
                    chat_id=chat_id,
                    video=media_input,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML,
                )
            elif media_type == MediaType.GIF and media_input:
                await bot.send_animation(
                    chat_id=chat_id,
                    animation=media_input,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML,
                )
            else:
                await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML,
                )
        except Exception as e:
            logger.error("Ошибка при отправке кастомного старт-сообщения", error=str(e))
            # Fallback
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )

    return True


async def try_handle_custom_notification(
    bot: Bot,
    user: User,
    notification_type_val: str,
    context: dict[str, Any],
    fallback_markup: Any = None,
) -> bool:
    """Обрабатывает и отправляет кастомное уведомление, если для него настроен шаблон.

    Возвращает True, если уведомление отправлено по кастомному шаблону.
    Возвращает False, если кастомизация выключена или шаблон не настроен (делегирует стандарту).
    """
    if not customization_service.is_enabled():
        return False

    config = customization_service.get_cached_config()
    custom_data = format_custom_notification(
        config=config,
        notification_type=notification_type_val,
        language=user.language or config.default_language or "ru",
        context=context,
    )

    if not custom_data:
        return False

    text = custom_data["text"]
    media_type = custom_data["media_type"]
    media_url = custom_data["media_url"].strip()
    buttons = custom_data["buttons"]

    keyboard = build_custom_inline_keyboard(buttons, language=user.language or "ru") if buttons else fallback_markup

    media_input = None
    if media_url:
        if os.path.exists(media_url):
            media_input = FSInputFile(media_url)
        else:
            media_input = media_url

    try:
        if media_type == MediaType.PHOTO and media_input:
            await bot.send_photo(
                chat_id=user.telegram_id,
                photo=media_input,
                caption=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
        elif media_type == MediaType.VIDEO and media_input:
            await bot.send_video(
                chat_id=user.telegram_id,
                video=media_input,
                caption=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
        elif media_type == MediaType.GIF and media_input:
            await bot.send_animation(
                chat_id=user.telegram_id,
                animation=media_input,
                caption=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
        else:
            await bot.send_message(
                chat_id=user.telegram_id,
                text=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
        return True
    except Exception as e:
        logger.error("Ошибка отправки кастомного уведомления", notif_type=notification_type_val, error=str(e))
        return False
