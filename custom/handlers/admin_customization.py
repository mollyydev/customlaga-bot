from __future__ import annotations

import structlog
from aiogram import Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.localization.texts import get_texts
from app.utils.decorators import admin_required, error_handler
from custom.services.customization_service import customization_service


logger = structlog.get_logger(__name__)


def get_admin_customization_keyboard(enabled: bool, language: str = "ru") -> InlineKeyboardMarkup:
    texts = get_texts(language)
    status_emoji = "🟢" if enabled else "🔴"
    toggle_text = f"{status_emoji} Статус: {'ВКЛЮЧЕНА' if enabled else 'ОТКЛЮЧЕНА'}"

    # We can provide a direct link / webapp button to /customization
    from app.config import settings
    base_url = settings.get_cabinet_allowed_origins()
    # Try to pick first origin or localhost fallback
    panel_url = f"{base_url[0].rstrip('/')}/customization" if (base_url and base_url[0] != "*") else "/customization"

    buttons = [
        [
            InlineKeyboardButton(
                text=toggle_text,
                callback_data="admin_customization_toggle",
            )
        ],
        [
            InlineKeyboardButton(
                text="🌐 Открыть веб-панель конструктора",
                url=panel_url if panel_url.startswith("http") else None,
                web_app=WebAppInfo(url=panel_url) if not panel_url.startswith("http") else None,
            )
        ],
        [
            InlineKeyboardButton(
                text="💾 Синхронизировать в JSON",
                callback_data="admin_customization_sync",
            )
        ],
        [
            InlineKeyboardButton(
                text=texts.BACK,
                callback_data="admin_settings",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@admin_required
@error_handler
async def show_admin_customization(callback: types.CallbackQuery, db_user: User, db: AsyncSession):
    config = await customization_service.get_config(db)
    
    text = (
        "🎨 **Конструктор и кастомизация бота**\n\n"
        f"• Статус кастомизации: **{'Включена (настройки активны)' if config.enabled else 'Отключена (стандартный бот)'}**\n"
        f"• Режим работы: **{'Real-time (внесены изменения)' if config.needs_restart else 'Синхронизировано (память/файл)'}**\n"
        f"• Автоопределение языка: **{'Включено' if config.auto_detect_language else 'Отключено'}**\n"
        f"• Язык по умолчанию: **{config.default_language}**\n"
        f"• Сценарий /start: **{config.start_flow.scenario.value}**\n\n"
        "💡 Для тонкой настройки страниц, медиа-файлов, кнопок и уведомлений откройте веб-панель."
    )
    if config.needs_restart:
        text += "\n\n⚠️ _Внимание: внесены изменения! Рекомендуется перезапустить бота для фиксации данных._"

    keyboard = get_admin_customization_keyboard(config.enabled, db_user.language)
    if callback.message:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@admin_required
@error_handler
async def cmd_admin_customization(message: types.Message, db_user: User, db: AsyncSession):
    config = await customization_service.get_config(db)
    text = (
        "🎨 **Конструктор и кастомизация бота**\n\n"
        f"• Статус: **{'Включена' if config.enabled else 'Отключена'}**\n"
        "Для управления перейдите по кнопке ниже:"
    )
    keyboard = get_admin_customization_keyboard(config.enabled, db_user.language)
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")


@admin_required
@error_handler
async def toggle_admin_customization(callback: types.CallbackQuery, db_user: User, db: AsyncSession):
    config = await customization_service.get_config(db)
    new_status = not config.enabled
    await customization_service.update_config(db, {"enabled": new_status})
    await show_admin_customization(callback, db_user, db)


@admin_required
@error_handler
async def sync_admin_customization(callback: types.CallbackQuery, db_user: User, db: AsyncSession):
    await customization_service.sync_to_disk()
    await callback.answer("✅ Конфигурация сохранена в файл JSON!", show_alert=True)
    await show_admin_customization(callback, db_user, db)


def register_handlers(dp: Dispatcher):
    dp.callback_query.register(show_admin_customization, F.data == "admin_customization")
    dp.callback_query.register(toggle_admin_customization, F.data == "admin_customization_toggle")
    dp.callback_query.register(sync_admin_customization, F.data == "admin_customization_sync")
    dp.message.register(cmd_admin_customization, Command("customization"))
