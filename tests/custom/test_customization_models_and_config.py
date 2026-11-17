
from custom.config import (
    ButtonConfig,
    ButtonTargetType,
    CustomizationConfig,
    MediaType,
    PageConfig,
    StartScenario,
)


def test_default_customization_config():
    config = CustomizationConfig()
    assert config.enabled is False
    assert config.default_language == 'ru'
    assert config.auto_detect_language is True
    assert config.needs_restart is False
    assert 'main' in config.pages
    assert 'subscription' in config.pages
    assert config.start_flow.scenario == StartScenario.DEFAULT


def test_button_config_validation():
    btn = ButtonConfig(
        id='sub_btn',
        is_builtin=True,
        target_type=ButtonTargetType.PAGE,
        target_value='subscription',
        text={'ru': 'Подписка', 'en': 'Subscription'},
        emoji='💎',
        enabled=True,
    )
    assert btn.id == 'sub_btn'
    assert btn.is_builtin is True
    assert btn.target_type == ButtonTargetType.PAGE
    assert btn.target_value == 'subscription'
    assert btn.text['ru'] == 'Подписка'
    assert btn.enabled is True

    # Custom button test
    custom_btn = ButtonConfig(
        id='about_btn',
        is_builtin=False,
        target_type=ButtonTargetType.PAGE,
        target_value='about',
        text={'ru': 'О нас', 'en': 'About us'},
        enabled=True,
    )
    assert custom_btn.is_builtin is False


def test_page_config():
    page = PageConfig(
        id='main',
        title='Главная',
        media_type=MediaType.PHOTO,
        media_url='assets/main.png',
        text={
            'ru': 'Привет, {user_name}! Добро пожаловать.',
            'en': 'Hello, {user_name}! Welcome.',
        },
        buttons=[
            ButtonConfig(
                id='btn_sub',
                is_builtin=True,
                target_type=ButtonTargetType.PAGE,
                target_value='subscription',
                text={'ru': 'Подписка'},
            )
        ],
    )
    assert page.id == 'main'
    assert page.media_type == MediaType.PHOTO
    assert len(page.buttons) == 1


def test_serialization_roundtrip():
    config = CustomizationConfig()
    config.enabled = True
    config.start_flow.scenario = StartScenario.FIRST_START_TUTORIAL
    config.start_flow.first_message.text['ru'] = 'Инструкция для новичка'

    d = config.to_dict()
    assert d['enabled'] is True
    assert d['start_flow']['scenario'] == 'first_start_tutorial'

    restored = CustomizationConfig.from_dict(d)
    assert restored.enabled is True
    assert restored.start_flow.scenario == StartScenario.FIRST_START_TUTORIAL
    assert restored.start_flow.first_message.text['ru'] == 'Инструкция для новичка'

    # JSON string serialization
    json_str = config.to_json()
    from_json = CustomizationConfig.from_json(json_str)
    assert from_json.enabled is True
    assert from_json.start_flow.scenario == StartScenario.FIRST_START_TUTORIAL
