from __future__ import annotations

import re
from typing import Any
import structlog


logger = structlog.get_logger(__name__)


class EmojiService:
    """Сервис для работы с Telegram Premium / Custom эмодзи."""

    _cached_packs: list[dict[str, Any]] = []

    def format_tg_emoji(self, emoji_id: str, fallback_char: str = "✨") -> str:
        """Форматирует тег кастомного эмодзи для Telegram HTML parse_mode."""
        if not emoji_id:
            return fallback_char
        return f'<tg-emoji emoji-id="{emoji_id}">{fallback_char}</tg-emoji>'

    async def add_emoji_pack(self, url: str, name: str | None = None) -> dict[str, Any]:
        """Обрабатывает и сохраняет ссылку на набор эмодзи.

        Поддерживает ссылки вида:
        https://t.me/addemoji/pack_name
        tg://addemoji?set=pack_name
        """
        match = re.search(r"(?:addemoji/|set=)([a-zA-Z0-9_-]+)", url)
        pack_name = match.group(1) if match else (name or "custom_pack")

        pack_info = {
            "name": pack_name,
            "url": url,
            "count": 0,
            "emojis": [],
        }

        logger.info("Добавлен набор премиум эмодзи", pack_name=pack_name, url=url)
        return pack_info


emoji_service = EmojiService()
