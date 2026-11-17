from __future__ import annotations

import re
import urllib.parse
from typing import Any

import httpx
import structlog


logger = structlog.get_logger(__name__)

SUPPORTED_LANGUAGES: list[str] = ["ru", "en", "ua", "zh", "fa"]

# Mapping between Telegram/BCP-47 language codes and internal codes
_CODE_NORMALIZATION: dict[str, str] = {
    "uk": "ua",
    "ua": "ua",
    "ru": "ru",
    "en": "en",
    "zh": "zh",
    "fa": "fa",
}


def detect_user_language(telegram_language_code: str | None, default_lang: str = "ru") -> str:
    """Определяет язык пользователя по его коду в Telegram.

    - Если код начинается на 'ru' -> 'ru'
    - Если код в списке поддерживаемых -> нормализованный код (например uk -> ua)
    - Если не поддерживается или None -> default_lang
    """
    if not telegram_language_code or not isinstance(telegram_language_code, str):
        return default_lang

    clean = telegram_language_code.strip().lower()
    # Extract primary subtag (e.g. 'ru-RU' -> 'ru', 'en_US' -> 'en')
    base = re.split(r"[-_]", clean)[0]

    normalized = _CODE_NORMALIZATION.get(base, base)
    if normalized in SUPPORTED_LANGUAGES:
        return normalized

    return default_lang


async def _translate_single_text(text: str, source_lang: str, target_lang: str) -> str:
    """Выполняет перевод через бесплатный эндпоинт Google Translate."""
    if not text.strip() or source_lang == target_lang:
        return text

    # Map internal code to Google translate code
    gt_source = "uk" if source_lang == "ua" else source_lang
    gt_target = "uk" if target_lang == "ua" else target_lang

    url = (
        f"https://translate.googleapis.com/translate_a/single"
        f"?client=gtx&sl={gt_source}&tl={gt_target}&dt=t&q={urllib.parse.quote(text)}"
    )

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                # Google returns [[['translated_sentence', 'orig_sentence', ...], ...]]
                translated_parts = [segment[0] for segment in data[0] if segment and segment[0]]
                return "".join(translated_parts)
    except Exception as exc:
        logger.warning(
            "Не удалось перевести текст через Google Translate, используется оригинал",
            error=str(exc),
            source=source_lang,
            target=target_lang,
        )

    return text


async def auto_translate_text(
    text: str,
    source_lang: str = "ru",
    target_langs: list[str] | None = None,
) -> dict[str, str]:
    """Автоматически переводит текст на целевые языки.

    Возвращает словарь {lang: translated_text}.
    """
    if target_langs is None:
        target_langs = [lang for lang in SUPPORTED_LANGUAGES if lang != source_lang]

    results: dict[str, str] = {source_lang: text}
    for target in target_langs:
        if target == source_lang:
            continue
        translated = await _translate_single_text(text, source_lang, target)
        results[target] = translated

    return results
