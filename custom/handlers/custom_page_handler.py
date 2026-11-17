from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import structlog
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from custom.config import ButtonTargetType, MediaType, PageConfig
from custom.services.customization_service import customization_service


logger = structlog.get_logger(__name__)


# Standard mappings for builtin actions to existing callbacks/commands
BUILTIN_ACTION_CALLBACKS: dict[str, str] = {
    "connect": "connect",
    "subscription": "subscription",
    "buy_subscription": "subscription_new",
    "balance": "balance",
    "support": "support",
    "main": "main_menu",
    "promocode": "promocode",
    "referrals": "referrals",
    "trial": "trial",
}


def build_custom_inline_keyboard(buttons: list[dict[str, Any]], language: str = "ru") -> InlineKeyboardMarkup:
    """Формирует InlineKeyboardMarkup из списка кнопок кастомизации."""
    rows: dict[int, list[InlineKeyboardButton]] = {}

    for btn in buttons:
        if not btn.get("enabled", True):
            continue

        raw_text = (btn.get("text") or {}).get(language) or (btn.get("text") or {}).get("ru") or btn.get("id", "")
        emoji = btn.get("emoji", "")
        text = f"{emoji} {raw_text}".strip() if emoji else raw_text

        target_type = btn.get("target_type", "builtin")
        target_value = btn.get("target_value", "")
        row_idx = btn.get("row", 0)

        ikb = None
        if target_type == "url" and target_value:
            ikb = InlineKeyboardButton(text=text, url=target_value)
        elif target_type == "webapp" and target_value:
            ikb = InlineKeyboardButton(text=text, web_app=WebAppInfo(url=target_value))
        elif target_type == "page" and target_value:
            if target_value == "main":
                ikb = InlineKeyboardButton(text=text, callback_data="main_menu")
            else:
                ikb = InlineKeyboardButton(text=text, callback_data=f"custom_page:{target_value}")
        elif target_type == "builtin":
            cb_data = BUILTIN_ACTION_CALLBACKS.get(target_value, target_value or "main_menu")
            ikb = InlineKeyboardButton(text=text, callback_data=cb_data)
        else:
            ikb = InlineKeyboardButton(text=text, callback_data=f"custom_btn:{btn.get('id')}")

        if ikb:
            rows.setdefault(row_idx, []).append(ikb)

    sorted_rows = [rows[k] for k in sorted(rows.keys())]
    return InlineKeyboardMarkup(inline_keyboard=sorted_rows)


async def send_custom_page_message(
    bot: Bot,
    chat_id: int,
    page: PageConfig,
    language: str = "ru",
    user_name: str = "",
    extra_context: dict[str, Any] | None = None,
) -> types.Message | None:
    """Отправляет кастомную страницу пользователю с медиа и кнопками."""
    raw_text = page.text.get(language) or page.text.get("ru") or ""
    
    # Render placeholders
    rendered_text = raw_text.replace("{user_name}", user_name)
    if extra_context:
        for k, v in extra_context.items():
            rendered_text = rendered_text.replace(f"{{{k}}}", str(v))

    keyboard = build_custom_inline_keyboard(
        [b.to_dict() for b in page.buttons], language=language
    )

    media_type = page.media_type
    media_url = page.media_url.strip()

    # Determine input media (local file or URL)
    media_input = None
    if media_url:
        if os.path.exists(media_url):
            media_input = FSInputFile(media_url)
        else:
            media_input = media_url

    try:
        if media_type == MediaType.PHOTO and media_input:
            return await bot.send_photo(
                chat_id=chat_id,
                photo=media_input,
                caption=rendered_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
        elif media_type == MediaType.VIDEO and media_input:
            return await bot.send_video(
                chat_id=chat_id,
                video=media_input,
                caption=rendered_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
        elif media_type == MediaType.GIF and media_input:
            return await bot.send_animation(
                chat_id=chat_id,
                animation=media_input,
                caption=rendered_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
        else:
            return await bot.send_message(
                chat_id=chat_id,
                text=rendered_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
    except Exception as exc:
        logger.error("Ошибка отправки кастомной страницы", page_id=page.id, error=str(exc))
        # Fallback to plain text message
        return await bot.send_message(
            chat_id=chat_id,
            text=rendered_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )


async def handle_custom_page_callback(callback: types.CallbackQuery, db_user: User, db: AsyncSession):
    """Обработчик перехода по страницам конструктора."""
    if not callback.data:
        return

    page_id = callback.data.split("custom_page:", 1)[1]
    page = customization_service.get_page(page_id)
    if not page:
        await callback.answer("Страница не найдена", show_alert=True)
        return

    # Delete or edit message
    if callback.message:
        try:
            await callback.message.delete()
        except Exception:
            pass

    user_name = db_user.full_name or callback.from_user.full_name or ""
    await send_custom_page_message(
        bot=callback.bot,
        chat_id=callback.from_user.id,
        page=page,
        language=db_user.language or "ru",
        user_name=user_name,
    )
    await callback.answer()


def register_handlers(dp: Dispatcher):
    dp.callback_query.register(handle_custom_page_callback, F.data.startswith("custom_page:"))
