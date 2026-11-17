from unittest.mock import AsyncMock, patch

import pytest

from custom.services.language_service import (
    auto_translate_text,
    detect_user_language,
)


def test_detect_user_language():
    # Russian detection
    assert detect_user_language('ru', default_lang='en') == 'ru'
    assert detect_user_language('ru-RU', default_lang='en') == 'ru'
    assert detect_user_language('ru_RU', default_lang='en') == 'ru'

    # Supported foreign languages
    assert detect_user_language('en', default_lang='ru') == 'en'
    assert detect_user_language('en-US', default_lang='ru') == 'en'
    assert detect_user_language('uk', default_lang='ru') == 'ua'
    assert detect_user_language('ua', default_lang='ru') == 'ua'

    # Unsupported language -> fallback to default
    assert detect_user_language('es', default_lang='ru') == 'ru'
    assert detect_user_language('de', default_lang='ru') == 'ru'
    assert detect_user_language(None, default_lang='ru') == 'ru'
    assert detect_user_language('fr', default_lang='en') == 'en'


@pytest.mark.asyncio
async def test_auto_translate_text():
    # Test translate service
    with patch('custom.services.language_service._translate_single_text', new_callable=AsyncMock) as mock_tr:
        mock_tr.side_effect = lambda text, src, target: f'[{target}] {text}'

        results = await auto_translate_text('Привет', source_lang='ru', target_langs=['en', 'ua'])
        assert results['en'] == '[en] Привет'
        assert results['ua'] == '[ua] Привет'
