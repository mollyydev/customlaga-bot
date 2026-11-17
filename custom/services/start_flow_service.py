from __future__ import annotations

import html
from typing import Any

from custom.config import (
    ButtonConfig,
    ButtonTargetType,
    CustomizationConfig,
    MediaType,
    StartScenario,
)


def _render_text(raw_text: str, user_name: str = "", extra_context: dict[str, Any] | None = None) -> str:
    ctx = {"user_name": html.escape(user_name or "")}
    if extra_context:
        for k, v in extra_context.items():
            ctx[k] = html.escape(str(v)) if isinstance(v, str) else v
    try:
        return raw_text.format(**ctx)
    except KeyError:
        # Fallback if any placeholder missing in text
        formatted = raw_text
        for k, v in ctx.items():
            formatted = formatted.replace(f"{{{k}}}", str(v))
        return formatted


def get_custom_start_messages(
    config: CustomizationConfig,
    user_name: str = "",
    language: str = "ru",
    is_first_time: bool = False,
    extra_context: dict[str, Any] | None = None,
) -> list[dict[str, Any]] | None:
    """Возвращает список сообщений для отправки при команде /start.

    Если кастомизация выключена -> возвращает None (делегирует штатной логике бота).
    """
    if not config.enabled:
        return None

    scenario = config.start_flow.scenario
    messages: list[dict[str, Any]] = []

    # Главное сообщение (страница 'main')
    main_page = config.pages.get("main")
    main_text_raw = (
        main_page.text.get(language) or main_page.text.get("ru") or "👋 Добро пожаловать!"
        if main_page
        else "👋 Добро пожаловать!"
    )
    main_text = _render_text(main_text_raw, user_name=user_name, extra_context=extra_context)
    main_media_type = main_page.media_type if main_page else MediaType.NONE
    main_media_url = main_page.media_url if main_page else ""
    main_buttons = main_page.buttons if main_page else []

    main_msg_dict = {
        "text": main_text,
        "media_type": main_media_type,
        "media_url": main_media_url,
        "buttons": [b.to_dict() for b in main_buttons if b.enabled],
        "is_main_menu": True,
    }

    # Первое/вводное сообщение (из start_flow.first_message)
    first_msg_raw = (
        config.start_flow.first_message.text.get(language)
        or config.start_flow.first_message.text.get("ru")
        or ""
    )
    first_text = _render_text(first_msg_raw, user_name=user_name, extra_context=extra_context)
    first_msg_dict = {
        "text": first_text,
        "media_type": config.start_flow.first_message.media_type,
        "media_url": config.start_flow.first_message.media_url,
        "buttons": [b.to_dict() for b in config.start_flow.first_message.buttons if b.enabled],
        "is_main_menu": False,
    }

    if scenario == StartScenario.DEFAULT:
        messages.append(main_msg_dict)
    elif scenario == StartScenario.FIRST_START_TUTORIAL:
        if is_first_time:
            if first_text.strip() or first_msg_dict["media_url"]:
                messages.append(first_msg_dict)
            messages.append(main_msg_dict)
        else:
            messages.append(main_msg_dict)
    elif scenario == StartScenario.ALWAYS_TWO_MESSAGES:
        if first_text.strip() or first_msg_dict["media_url"]:
            messages.append(first_msg_dict)
        messages.append(main_msg_dict)

    return messages
