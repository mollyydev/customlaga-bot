from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom.bot_integration import setup_customization, try_handle_custom_notification, try_handle_custom_start
from custom.config import CustomizationConfig, MediaType, NotificationConfig, StartScenario


@pytest.mark.asyncio
async def test_setup_customization():
    mock_dp = MagicMock()
    mock_bot = MagicMock()
    await setup_customization(mock_dp, mock_bot)
    assert mock_dp.callback_query.register.called
    assert mock_dp.message.register.called


@pytest.mark.asyncio
async def test_try_handle_custom_start_disabled():
    with patch('custom.bot_integration.customization_service.is_enabled', return_value=False):
        mock_msg = AsyncMock()
        mock_state = AsyncMock()
        mock_db = AsyncMock()
        handled = await try_handle_custom_start(mock_msg, mock_state, mock_db)
        assert handled is False


@pytest.mark.asyncio
async def test_try_handle_custom_start_enabled_with_autodetect():
    config = CustomizationConfig(enabled=True, auto_detect_language=True)
    config.start_flow.scenario = StartScenario.DEFAULT
    config.pages['main'].text['ru'] = 'Главная {user_name}'

    with patch('custom.bot_integration.customization_service.is_enabled', return_value=True), \
         patch('custom.bot_integration.customization_service.get_cached_config', return_value=config):

        mock_msg = AsyncMock()
        mock_msg.chat.id = 12345
        mock_msg.from_user.language_code = 'ru-RU'
        mock_msg.from_user.full_name = 'Alex'
        mock_bot = AsyncMock()
        mock_msg.bot = mock_bot
        mock_state = AsyncMock()
        mock_state.get_data.return_value = {}
        mock_db = AsyncMock()

        handled = await try_handle_custom_start(mock_msg, mock_state, mock_db, is_first_time=False)
        assert handled is True
        assert mock_bot.send_message.called
        sent_text = mock_bot.send_message.call_args.kwargs['text']
        assert 'Главная Alex' in sent_text


@pytest.mark.asyncio
async def test_try_handle_custom_notification():
    config = CustomizationConfig(enabled=True)
    config.notifications['subscription_expiring'] = NotificationConfig(
        enabled=True,
        text={'ru': 'Подписка истекает через {days_left} дней!'},
        media_type=MediaType.NONE,
    )

    with patch('custom.bot_integration.customization_service.is_enabled', return_value=True), \
         patch('custom.bot_integration.customization_service.get_cached_config', return_value=config):

        mock_bot = AsyncMock()
        mock_user = MagicMock()
        mock_user.telegram_id = 12345
        mock_user.language = 'ru'

        handled = await try_handle_custom_notification(
            bot=mock_bot,
            user=mock_user,
            notification_type_val='subscription_expiring',
            context={'days_left': 3},
        )
        assert handled is True
        assert mock_bot.send_message.called
        assert 'через 3 дней' in mock_bot.send_message.call_args.kwargs['text']
