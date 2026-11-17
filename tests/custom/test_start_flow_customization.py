
from custom.config import (
    CustomizationConfig,
    MediaType,
    StartFlowMessage,
    StartScenario,
)
from custom.services.start_flow_service import get_custom_start_messages


def test_start_flow_disabled():
    config = CustomizationConfig(enabled=False)
    # When disabled, returns None indicating standard upstream flow should execute
    messages = get_custom_start_messages(config, user_name='Alex', language='ru', is_first_time=True)
    assert messages is None


def test_start_flow_scenario_default():
    config = CustomizationConfig(enabled=True)
    config.start_flow.scenario = StartScenario.DEFAULT
    config.pages['main'].text['ru'] = 'Главная страница'

    messages = get_custom_start_messages(config, user_name='Alex', language='ru', is_first_time=False)
    assert messages is not None
    assert len(messages) == 1
    assert 'Главная страница' in messages[0]['text']


def test_start_flow_first_start_tutorial():
    config = CustomizationConfig(enabled=True)
    config.start_flow.scenario = StartScenario.FIRST_START_TUTORIAL
    config.start_flow.first_message = StartFlowMessage(
        text={'ru': 'Добро пожаловать в VPN! Краткий туториал: ...'},
        media_type=MediaType.PHOTO,
        media_url='assets/tutorial.png',
    )
    config.pages['main'].text['ru'] = 'Основное меню бота'

    # First time user
    first_time_messages = get_custom_start_messages(config, user_name='Alex', language='ru', is_first_time=True)
    assert first_time_messages is not None
    assert len(first_time_messages) == 2
    assert 'Краткий туториал' in first_time_messages[0]['text']
    assert first_time_messages[0]['media_url'] == 'assets/tutorial.png'
    assert 'Основное меню бота' in first_time_messages[1]['text']

    # Returning user
    returning_messages = get_custom_start_messages(config, user_name='Alex', language='ru', is_first_time=False)
    assert returning_messages is not None
    assert len(returning_messages) == 1
    assert 'Основное меню бота' in returning_messages[0]['text']


def test_start_flow_always_two_messages():
    config = CustomizationConfig(enabled=True)
    config.start_flow.scenario = StartScenario.ALWAYS_TWO_MESSAGES
    config.start_flow.first_message = StartFlowMessage(
        text={'ru': 'Информационный баннер'},
        media_type=MediaType.NONE,
    )
    config.pages['main'].text['ru'] = 'Основное меню'

    # Both first-time and returning get 2 messages
    msg1 = get_custom_start_messages(config, user_name='Alex', language='ru', is_first_time=True)
    assert len(msg1) == 2
    assert 'Информационный баннер' in msg1[0]['text']
    assert 'Основное меню' in msg1[1]['text']

    msg2 = get_custom_start_messages(config, user_name='Alex', language='ru', is_first_time=False)
    assert len(msg2) == 2
    assert 'Информационный баннер' in msg2[0]['text']
    assert 'Основное меню' in msg2[1]['text']
