from __future__ import annotations

import html
from typing import Any

from custom.config import CustomizationConfig, MediaType


def format_custom_notification(
    config: CustomizationConfig,
    notification_type: str,
    language: str = "ru",
    context: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Форматирует кастомное уведомление, если для него настроен шаблон.

    Если кастомизация выключена или шаблон отсутствует -> возвращает None.
    """
    if not config.enabled:
        return None

    notif_config = config.notifications.get(notification_type)
    if not notif_config or not notif_config.enabled:
        return None

    raw_text = notif_config.text.get(language) or notif_config.text.get("ru")
    if not raw_text:
        return None

    ctx = {}
    if context:
        for k, v in context.items():
            ctx[k] = html.escape(str(v)) if isinstance(v, str) else v

    try:
        formatted_text = raw_text.format(**ctx)
    except KeyError:
        formatted_text = raw_text
        for k, v in ctx.items():
            formatted_text = formatted_text.replace(f"{{{k}}}", str(v))

    return {
        "text": formatted_text,
        "media_type": notif_config.media_type,
        "media_url": notif_config.media_url,
        "buttons": [b.to_dict() for b in notif_config.buttons if b.enabled],
    }
